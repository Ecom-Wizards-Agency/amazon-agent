#!/usr/bin/env python3
"""Post one copy-ready inventory overview thread through the Wizards AI helper."""

import argparse
import json
from pathlib import Path

import slack_helper


def run_helper(_helper, *args: str) -> dict:
    return json.loads(slack_helper.run_helper(*args))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--message-file", required=True)
    args = parser.parse_args()

    helper = None  # resolved per-OS by slack_helper
    message = Path(args.message_file).read_text(encoding="utf-8").strip()
    if "\n*Reshipment*\nNo positive reshipment quantities" in message:
        raise SystemExit(
            "Account has no positive reshipment quantity. Add it to the grouped "
            "'No reshipment needed for' parent instead."
        )
    source, reshipment_and_excess = message.split("\n\n*Reshipment*\n", 1)
    if "\n\n*Excess Inventory / Plan Sales*\n" in reshipment_and_excess:
        reshipment, excess = reshipment_and_excess.split(
            "\n\n*Excess Inventory / Plan Sales*\n", 1
        )
    else:
        reshipment, excess = reshipment_and_excess, None

    validation_line = (
        "• FBA 7d/30d: validation context; Restock: unavailable for this marketplace"
        if "does not expose the Restock report" in source
        else "• FBA 7d/30d and Restock data: validation and fallback context"
    )
    calculation = "\n".join(
        [
            "*How it was calculated*",
            "• Demand: Business Report units ordered over the last 30 days",
            "• Required units: (30d demand ÷ 30) × scaling multiplier × effective coverage days",
            "• Reshipment: round up max(0, required units - available - inbound - reserved)",
            validation_line,
            f"• {source}",
        ]
    )
    reshipment_message = f"*Reshipment*\n{reshipment}"

    parent = run_helper(helper, "post", args.channel, f"*{args.title}*")
    thread_ts = parent["ts"]
    run_helper(helper, "post", args.channel, calculation, thread_ts)
    run_helper(helper, "post", args.channel, reshipment_message, thread_ts)
    if excess:
        excess_calculation = "\n".join(
            [
                "*Excess calculation*",
                "• Primary: Amazon estimated excess quantity from the FBA Inventory report",
                "• Fallback when Amazon gives no estimate: flag stock above 120 days of cover, then calculate available units minus 90 days of demand",
            ]
        )
        run_helper(
            helper,
            "post",
            args.channel,
            f"*Excess Inventory / Plan Sales*\n{excess_calculation}\n\n{excess}",
            thread_ts,
        )
    permalink = run_helper(helper, "permalink", args.channel, thread_ts)
    print(json.dumps({"title": args.title, "permalink": permalink["permalink"]}))


if __name__ == "__main__":
    main()
