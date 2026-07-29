#!/usr/bin/env python3
"""Post the grouped no-reshipment parent through the Wizards AI helper."""

import argparse
import json

import slack_helper


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True)
    parser.add_argument("--brand", action="append", required=True)
    parser.add_argument("--thread-ts")
    args = parser.parse_args()

    message = "*No reshipment needed for:*\n" + "\n".join(
        f"• {brand}" for brand in args.brand
    )
    post_args = ["post", args.channel, message]
    if args.thread_ts:
        post_args.append(args.thread_ts)
    posted = json.loads(slack_helper.run_helper(*post_args))
    parent_ts = args.thread_ts or posted["ts"]
    permalink = json.loads(
        slack_helper.run_helper("permalink", args.channel, parent_ts)
    )["permalink"]
    print(json.dumps({"permalink": permalink}))


if __name__ == "__main__":
    main()
