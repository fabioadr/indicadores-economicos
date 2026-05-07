#!/usr/bin/env python3
"""Reproduce IBGE SIDRA fetch in isolation (no full pipeline)."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline.connectors.ibge_sidra import IBGESIDRAConnector  # noqa: E402


def _parse_since(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch one IBGE SIDRA series via IBGESIDRAConnector."
    )
    parser.add_argument("tabela", type=int, help="SIDRA tabela id (e.g. 3065 for IPCA-15)")
    parser.add_argument("variavel", type=int, help="SIDRA variavel id (e.g. 355)")
    parser.add_argument(
        "--localidade", default="N1[all]", help="Localidade (default: N1[all])"
    )
    parser.add_argument(
        "--classificacao", default=None, help="Classificacao opcional (ex: '315[7169]')"
    )
    parser.add_argument(
        "--since",
        default="2024-01-01",
        help="Start date YYYY-MM-DD (default: 2024-01-01)",
    )
    args = parser.parse_args()
    config: dict = {
        "tabela": args.tabela,
        "variavel": args.variavel,
        "localidade": args.localidade,
    }
    if args.classificacao:
        config["classificacao"] = args.classificacao
    since = _parse_since(args.since)
    rows = IBGESIDRAConnector().fetch(config, since=since)
    print(f"rows: {len(rows)}")
    if rows:
        print(f"first: {rows[0]}")
        print(f"last: {rows[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
