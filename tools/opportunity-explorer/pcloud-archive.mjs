import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import os from "node:os";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { Worker } from "node:worker_threads";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..", "..");

const TEAM_VAULT_ENV = "AMAZON_AGENT_TEAM_VAULT";
const TEAM_VAULT_POINTER = path.join(REPO, "_local", "team-vault-path.txt");
function firstLine(file) {
  try {
    for (const line of fs.readFileSync(file, "utf8").split("\n")) {
      const t = line.trim();
      if (t && !t.startsWith("#")) return t;
    }
  } catch { /* missing pointer file is normal */ }
  return "";
}

function expand(p) {
  return p.startsWith("~") ? path.join(process.env.HOME || "", p.slice(1)) : p;
}

/** Root of the shared team vault, or "" when there is none on this machine. */
export function teamVaultRoot() {
  for (const c of [process.env[TEAM_VAULT_ENV] || "", firstLine(TEAM_VAULT_POINTER), path.join(os.homedir(), "os", "agency")]) {
    if (!c) continue;
    const root = expand(c);
    if (fs.existsSync(path.join(root, "Clients"))) return root;
  }
  return "";
}

/** The canonical `slug:` from a client folder's hub-note frontmatter, or "". */
function hubNoteSlug(clientsDir, name) {
  let head;
  try {
    head = fs.readFileSync(path.join(clientsDir, name, `${name}.md`), "utf8").slice(0, 2048);
  } catch {
    return "";
  }
  if (!head.startsWith("---")) return "";
  for (const line of head.split("\n").slice(1)) {
    if (line.trim() === "---") break;
    if (line.startsWith("slug:")) return line.slice(5).trim().toLowerCase();
  }
  return "";
}

/** Client FOLDER NAME for this slug, per the vault hub notes. "" when unmatched. */
export function vaultClientName(vaultRoot, slug) {
  if (!vaultRoot || !slug) return "";
  const clientsDir = path.join(vaultRoot, "Clients");
  const wanted = slug.trim().toLowerCase();
  let folders;
  try {
    folders = fs.readdirSync(clientsDir)
      .filter((n) => fs.statSync(path.join(clientsDir, n)).isDirectory())
      .sort();
  } catch {
    return "";
  }
  for (const n of folders) if (hubNoteSlug(clientsDir, n) === wanted) return n;
  for (const n of folders) if (n.toLowerCase().replace(/ /g, "-") === wanted) return n;
  return "";
}

/** API-backed POE storage. Upload bytes flow through stdin, never payload files. */
export function pcloudCommand(args, { input } = {}) {
  const helper = process.env.POE_PCLOUD_SCRIPT || path.join(os.homedir(), "os", "company-ai-skills", "skills", "pcloud-api", "scripts", "pcloud.sh");
  const result = spawnSync(helper, args, { encoding: "utf8", timeout: 300000, maxBuffer: 4 * 1024 * 1024, input });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    const error = new Error((result.stderr || "pCloud command failed").trim());
    error.missing = /API error (2009|2055)/.test(result.stderr || "");
    throw error;
  }
  return result.stdout.trim();
}

const sha1 = (bytes) => crypto.createHash("sha1").update(bytes).digest("hex");

export function prepareArchive(slug, { call = pcloudCommand, vault = teamVaultRoot() } = {}) {
  const client = vaultClientName(vault, slug);
  if (!client) throw new Error(`No canonical client for ${slug}; pCloud delivery is required before fetching POE`);
  const clientRoot = `1_Delivery/1.1_Clients/${client}`;
  call(["foldermeta", clientRoot]); // Never invent a client folder.
  call(["foldermeta", `${clientRoot}/_Data`]);
  const remote = `${clientRoot}/_Data/opportunity-data`;
  call(["mkdir", remote]);
  return { remote, call };
}

function checksum(call, remote) {
  try { return call(["checksum", remote]); }
  catch (error) { if (error.missing) return null; throw error; }
}

/** Publish in-memory formatter output; return only remote metadata. */
export function publishFiles(files, target) {
  if (!files.length) throw new Error("No POE files to publish");
  const { remote, call } = target;
  const artifacts = [];
  for (const file of files) {
    if (!file.name || path.basename(file.name) !== file.name || /[\\/]/.test(file.name) || [".", ".."].includes(file.name)) throw new Error("Invalid POE basename");
    const content = Buffer.isBuffer(file.content) ? file.content : Buffer.from(file.content);
    const hash = sha1(content);
    const existing = `${remote}/${file.name}`;
    // Reuse legacy names only when verified. New names are content-addressed,
    // so concurrent captures cannot overwrite different bytes at one path.
    const name = checksum(call, existing) === hash ? file.name : `${hash}_${file.name}`;
    const destination = `${remote}/${name}`;
    let status = "existing";
    const priorHash = checksum(call, destination);
    if (priorHash && priorHash !== hash) throw new Error(`Conflicting content-addressed path; not overwritten: ${destination}`);
    if (priorHash !== hash) {
      try { call(["put-stream", name, remote, hash], { input: content }); }
      catch (error) {
        if (checksum(call, destination) !== hash) throw error;
      }
      status = "uploaded";
    }
    if (checksum(call, destination) !== hash) throw new Error(`pCloud checksum mismatch: ${destination}`);
    artifacts.push({ name: file.name, remote_name: name, path: destination, sha1: hash, bytes: content.length, status });
  }
  return { remote_folder: remote, artifacts, status: "archived_verified", local_data_retained: false };
}

/** Keep the browser's heartbeat running during blocking pCloud helper calls. */
export function publishFilesAsync(files, { remote }) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(new URL("./pcloud-upload-worker.mjs", import.meta.url), {
      workerData: { files, remote },
    });
    let received = false;
    worker.once("message", receipt => { received = true; resolve(receipt); });
    worker.once("error", reject);
    worker.once("exit", code => {
      if (!received) reject(new Error(`POE upload worker exited ${code} without a verified receipt`));
    });
  });
}

/** Migrate an explicitly selected legacy directory. Remove only verified unchanged files. */
export function archiveClient(slug, { srcDir, dryRun = false, call = pcloudCommand, vault = teamVaultRoot() } = {}) {
  const source = path.resolve(srcDir || path.join(REPO, "output", slug, "opportunity-data"));
  if (fs.lstatSync(source).isSymbolicLink()) throw new Error("Refusing a symlink archive source");
  const files = [];
  function walk(dir) {
    for (const name of fs.readdirSync(dir).sort()) {
      const local = path.join(dir, name);
      const info = fs.lstatSync(local);
      if (info.isSymbolicLink()) throw new Error(`Refusing symlink: ${local}`);
      if (info.isDirectory()) walk(local);
      else if (info.isFile() && name !== ".DS_Store") files.push({ local, name, content: fs.readFileSync(local), ino: info.ino, dev: info.dev });
      else if (!info.isFile()) throw new Error(`Not a regular file: ${local}`);
    }
  }
  walk(source);
  if (!files.length) throw new Error("No POE files to archive");
  if (dryRun) return { status: "dry_run", source, files: files.map(f => f.local), local_data_retained: true };
  const target = prepareArchive(slug, { call, vault });
  const receipt = publishFiles(files, target);
  receipt.artifacts.forEach((artifact, i) => { artifact.source_relative_path = path.relative(source, files[i].local); });
  const manifestContent = JSON.stringify({ schema_version: 1, client: slug, files: receipt.artifacts }, null, 2);
  receipt.manifest = publishFiles([{ name: `${new Date().toISOString().slice(0, 7)}_POE_migration-manifest.json`, content: manifestContent }], target).artifacts[0];
  // Finish all network operations before checking source identity for deletion.
  for (const artifact of [...receipt.artifacts, receipt.manifest]) {
    if (checksum(call, artifact.path) !== artifact.sha1) throw new Error("Remote verification failed; kept sources");
  }
  function unchanged(file, artifact) {
    const info = fs.lstatSync(file.local);
    if (!info.isFile() || info.isSymbolicLink() || info.ino !== file.ino || info.dev !== file.dev || sha1(fs.readFileSync(file.local)) !== artifact.sha1) throw new Error(`Local POE changed; kept source: ${file.local}`);
  }
  for (const [i, file] of files.entries()) unchanged(file, receipt.artifacts[i]);
  for (const [i, file] of files.entries()) {
    unchanged(file, receipt.artifacts[i]);
    fs.unlinkSync(file.local);
  }
  return { ...receipt, removed_local_files: files.length, source };
}
