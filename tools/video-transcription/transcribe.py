#!/usr/bin/env python3
"""Whisper-transcribe a YouTube video, bypassing the caption path.

Audio-only download -> chunk under the 25 MB API cap -> whisper-1 (segment
timestamps) -> single timestamped transcript on stdout.

  transcribe.py VIDEO_ID [--backend openai|groq] [--out DIR]
"""
import argparse, json, os, pathlib, random, re, subprocess, sys, time, urllib.error, urllib.request


def with_retry(fn, attempts=5, what="request"):
    """Both YouTube and the transcription API drop connections under concurrency.
    Every failure seen in practice has been transient, so back off and retry."""
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            if i == attempts - 1:
                raise
            delay = min(2 ** i, 30) + random.uniform(0, 2)
            print(f"  retry {i+1}/{attempts-1} after {delay:.0f}s ({what}): "
                  f"{type(e).__name__}", file=sys.stderr)
            time.sleep(delay)

# The documented upload cap is 25 MB, but in practice the API drops the
# connection ("RemoteDisconnected") on bodies well below it: every video over
# ~19 min / ~9 MB failed, every one under ~13 min succeeded. Chunk small.
CAP = 5 * 1024 * 1024           # chunk anything over ~10 min of audio
CHUNK_SECS = 600                # 10 min at 64 kbps mono ≈ 4.8 MB
ENV = pathlib.Path.home() / ".config/watch/.env"

OPENAI_URL = "https://api.openai.com/v1/audio/transcriptions"

# diarize adds speaker labels (A/B/C) but costs ~3x and is weaker on casing and
# Amazon jargon — use it only for genuinely multi-speaker videos.
BACKENDS = {
    "openai":  (OPENAI_URL, "whisper-1", "OPENAI_API_KEY", "verbose_json"),
    "diarize": (OPENAI_URL, "gpt-4o-transcribe-diarize", "OPENAI_API_KEY", "diarized_json"),
    "groq":    ("https://api.groq.com/openai/v1/audio/transcriptions",
                "whisper-large-v3", "GROQ_API_KEY", "verbose_json"),
}


def key_for(var):
    for line in ENV.read_text().splitlines():
        if line.startswith(var + "="):
            return line.split("=", 1)[1].strip().strip("\"'")
    sys.exit(f"{var} not set in {ENV}")


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def fetch_audio(vid, workdir):
    """Download audio only, re-encoded mono 64 kbps to keep chunks small."""
    out = workdir / "audio.mp3"
    if not out.exists():
        with_retry(lambda: run(
            ["yt-dlp", "-f", "bestaudio", "-x", "--audio-format", "mp3",
             "--postprocessor-args", "-ac 1 -ar 16000 -b:a 64k",
             "--no-progress", "-o", str(workdir / "audio.%(ext)s"),
             f"https://www.youtube.com/watch?v={vid}"]), what="download")
    return out


def split(audio, workdir, chunk_secs=CHUNK_SECS, cap=CAP):
    """Return [(path, offset_seconds)] — one entry if the file already fits."""
    if audio.stat().st_size <= cap:
        return [(audio, 0.0)]
    for stale in workdir.glob("part*.mp3"):
        stale.unlink()
    run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(audio),
         "-f", "segment", "-segment_time", str(chunk_secs), "-c", "copy",
         str(workdir / "part%03d.mp3")])
    parts = sorted(workdir.glob("part*.mp3"))
    return [(p, i * chunk_secs) for i, p in enumerate(parts)]


def transcribe(path, url, model, key, fmt):
    """Multipart POST without external deps. Returns the parsed JSON body."""
    b = "----wb%s" % os.urandom(8).hex()
    fields = [("model", model), ("response_format", fmt)]
    if fmt == "diarized_json":
        fields.append(("chunking_strategy", "auto"))   # required by diarize models
    else:
        fields.append(("timestamp_granularities[]", "segment"))
    body = bytearray()
    for field, val in fields:
        body += (f"--{b}\r\nContent-Disposition: form-data; name=\"{field}\"\r\n\r\n{val}\r\n").encode()
    body += (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; "
             f"filename=\"{path.name}\"\r\nContent-Type: audio/mpeg\r\n\r\n").encode()
    body += path.read_bytes() + f"\r\n--{b}--\r\n".encode()
    payload = bytes(body)

    def post():
        req = urllib.request.Request(url, data=payload, method="POST", headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={b}"})
        with urllib.request.urlopen(req, timeout=900) as r:
            return json.loads(r.read())

    return with_retry(post, what=f"transcribe {path.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--backend", default="openai", choices=BACKENDS)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    url, model, keyvar, fmt = BACKENDS[a.backend]
    key = key_for(keyvar)
    workdir = pathlib.Path(a.out) / f"wd-{a.video_id}"
    workdir.mkdir(parents=True, exist_ok=True)

    audio = fetch_audio(a.video_id, workdir)
    title = json.loads(run(["yt-dlp", "--skip-download", "--print", "%(title)j",
                            f"https://www.youtube.com/watch?v={a.video_id}"]).stdout)

    print(f"# {title}\n\n- video_id: {a.video_id}")
    print(f"- url: https://www.youtube.com/watch?v={a.video_id}")
    print(f"- transcript: {model} via {a.backend}\n")

    # diarize's payload ceiling is far lower than whisper's — measured: 0.8 MB
    # succeeds, 1.1 MB and 2.3 MB both drop the connection, while whisper-1
    # handles 1.1 MB fine. Keep diarize chunks near 2 minutes / ~1 MB.
    chunk, cap = ((120, 900_000) if fmt == "diarized_json" else (CHUNK_SECS, CAP))

    # Speaker labels are only meaningful WITHIN a chunk — the model has no way to
    # tell that chunk 2's "A" is chunk 1's "A". Renumbering across chunks would
    # invent 26 speakers for a 2-person interview, so keep the raw per-chunk
    # letter and mark each boundary instead. Identity is stitched back together
    # by reading the content, not by trusting the letters across a boundary.
    parts = split(audio, workdir, chunk, cap)
    last = None
    for n, (part, offset) in enumerate(parts):
        if len(parts) > 1:
            print(f"\n<!-- speaker labels reset here (chunk {n + 1}/{len(parts)}) -->")
            last = None
        for seg in transcribe(part, url, model, key, fmt).get("segments", []):
            t = int(seg["start"] + offset)
            text = re.sub(r"\s+", " ", seg["text"]).strip()
            if not text:
                continue
            who = seg.get("speaker")
            prefix = "" if who is None or who == last else f"{who}: "
            last = who
            print(f"[{t//60:02d}:{t%60:02d}] {prefix}{text}")


if __name__ == "__main__":
    main()
