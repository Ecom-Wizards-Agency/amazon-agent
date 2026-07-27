#!/usr/bin/env python3
"""Post the grouped no-reshipment parent through the Wizards AI helper."""

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True)
    parser.add_argument("--brand", action="append", required=True)
    parser.add_argument("--thread-ts")
    args = parser.parse_args()

    helper = Path.home() / "Automations" / "wizards-ai" / "slack.sh"
    message = "*No reshipment needed for:*\n" + "\n".join(
        f"• {brand}" for brand in args.brand
    )
    helper_args = [str(helper), "post", args.channel, message]
    if args.thread_ts:
        helper_args.append(args.thread_ts)
    result = subprocess.run(
        helper_args,
        check=True,
        capture_output=True,
        text=True,
    )
    posted = json.loads(result.stdout)
    parent_ts = args.thread_ts or posted["ts"]
    permalink_result = subprocess.run(
        [str(helper), "permalink", args.channel, parent_ts],
        check=True,
        capture_output=True,
        text=True,
    )
    permalink = json.loads(permalink_result.stdout)["permalink"]
    print(json.dumps({"permalink": permalink}))


if __name__ == "__main__":
    main()
