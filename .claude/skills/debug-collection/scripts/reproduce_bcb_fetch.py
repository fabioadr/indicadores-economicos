#!/usr/bin/env python3
"""Reproduce BCB SGS fetch in isolation (no full pipeline)."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline.connectors.bcb import BCBSGSConnector  # noqa: E402


def _parse_since(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch one BCB SGS series via BCBSGSConnector.")
    parser.add_argument("series_id", type=int, help="SGS series id (e.g. 433 for IPCA)")
    parser.add_argument(
        "--since",
        default="2024-01-01",
        help="Start date YYYY-MM-DD (default: 2024-01-01)",
    )
    args = parser.parse_args()
    since = _parse_since(args.since)
    rows = BCBSGSConnector().fetch({"series_id": args.series_id}, since=since)
    print(f"rows: {len(rows)}")
    if rows:
        print(f"first: {rows[0]}")
        print(f"last: {rows[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
