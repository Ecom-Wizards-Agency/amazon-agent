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
    errors, warnings = validate(good_query, "query", "scheduled")
    require("valid scheduled measurement query", not errors, errors)
    require("valid scheduled query needs no warnings", not warnings, warnings)

    bad_query = "SELECT * FROM sponsored_ads_traffic ORDER BY spend DESC LIMIT 10"
    errors, _ = validate(bad_query, "query", "scheduled")
    require("unsafe measurement query is rejected", len(errors) >= 5, errors)

    observed_one_time_query = """
    WITH campaign_metrics AS (
      SELECT campaign, SUM(spend) AS spend_microcents, SUM(impressions) AS impressions,
             SUM(clicks) AS clicks
      FROM sponsored_ads_traffic
      GROUP BY 1
    ), campaign_metrics_with_totals AS (
      SELECT campaign, spend_microcents, impressions, clicks,
             SUM(spend_microcents) OVER () AS total_spend_microcents
      FROM campaign_metrics
    )
    SELECT campaign,
           CASE WHEN impressions = 0 THEN 0.0 ELSE 100.0 * clicks / impressions END AS ctr,
           CASE WHEN clicks = 0 THEN 0.0
                ELSE (spend_microcents / 100000000.0) / clicks END AS cpc,
           CASE WHEN total_spend_microcents = 0 THEN 0.0
                ELSE 100.0 * spend_microcents / total_spend_microcents END AS spend_share
    FROM campaign_metrics_with_totals
    ORDER BY spend_microcents DESC
    """
    errors, warnings = validate(observed_one_time_query, "query", "one-time")
    require("observed one-time SQL is accepted", not errors, errors)
    require("one-time date portability is disclosed", any(
        "execution date range" in warning for warning in warnings
    ), warnings)
    require("one-time outer sorting is disclosed", any(
        "outer ORDER BY" in warning for warning in warnings
    ), warnings)
    require("guarded CASE divisions are accepted", not any(
        "division by identifier" in warning for warning in warnings
    ), warnings)

    partial_window_query = """
    SELECT campaign, SUM(clicks) AS clicks
    FROM sponsored_ads_traffic
    WHERE event_date_utc >= BUILT_IN_PARAMETER('TIME_WINDOW_START')
    GROUP BY 1
    """
    errors, _ = validate(partial_window_query, "query", "one-time")
    require("partial one-time window tokens are rejected", len(errors) == 1, errors)

    errors, _ = validate("SELECT campaign FROM sponsored_ads_traffic LIMIT 10", "query", "one-time")
    require("outer LIMIT remains rejected for one-time SQL", any(
        "outer LIMIT" in error for error in errors
    ), errors)

    _, warnings = validate(
        "SELECT campaign, spend / clicks AS cpc FROM sponsored_ads_traffic",
        "query",
        "one-time",
    )
    require("unguarded identifier division is warned", any(
        "clicks" in warning for warning in warnings
    ), warnings)

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
