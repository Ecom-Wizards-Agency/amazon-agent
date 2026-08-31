#!/usr/bin/env python3
"""Regression checks for the AMC SQL validator."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from validate_sql import validate  # noqa: E402


def require(label: str, condition: bool, detail: object = "") -> None:
    if not condition:
        raise AssertionError(f"{label}: {detail}")
    print(f"PASS: {label}")


def main() -> int:
    good_query = """
    WITH b AS (
      SELECT campaign, COUNT(DISTINCT user_id) AS users, SUM(clicks) AS clicks
      FROM sponsored_ads_traffic
      WHERE event_date_utc BETWEEN BUILT_IN_PARAMETER('TIME_WINDOW_START')
                               AND BUILT_IN_PARAMETER('TIME_WINDOW_END')
      GROUP BY 1
    )
    SELECT campaign, users, clicks, 1.0 * clicks / NULLIF(users, 0) AS clicks_per_user
    FROM b
    """
    errors, warnings = validate(good_query, "query")
    require("valid measurement query", not errors, errors)
    require("valid query needs no division warning", not warnings, warnings)

    bad_query = "SELECT * FROM sponsored_ads_traffic ORDER BY spend DESC LIMIT 10"
    errors, _ = validate(bad_query, "query")
    require("unsafe measurement query is rejected", len(errors) >= 5, errors)

    good_audience = """
    WITH converters AS (
      SELECT user_id
      FROM amazon_attributed_events_by_conversion_time
      WHERE purchases > 0
      GROUP BY 1
    )
    SELECT user_id FROM converters
    """
    errors, _ = validate(good_audience, "audience")
    require("valid audience query", not errors, errors)

    bad_audience = """
    SELECT campaign
    FROM sponsored_ads_traffic
    WHERE event_date_utc >= BUILT_IN_PARAMETER('TIME_WINDOW_START')
    """
    errors, _ = validate(bad_audience, "audience")
    require("audience date and output violations are rejected", len(errors) == 2, errors)
    print("AMC validator selftest: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
