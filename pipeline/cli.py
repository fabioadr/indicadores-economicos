"""Pipeline CLI — entry point for collect, build, deploy, status, etc.

Milestone 0: argparse skeleton with no-op handlers. Real implementations land
in subsequent milestones (M1: migrate; M2: collect/backfill; M5: build; M9: deploy).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

VERSION = "0.0.1"
REPO_ROOT = Path(__file__).resolve().parent.parent


def _not_implemented(name: str) -> int:
    print(f"{name}: not implemented yet (Milestone 0 skeleton)")
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    return _not_implemented("migrate")


def cmd_collect(args: argparse.Namespace) -> int:
    if not args.all and not args.code:
        print("collect: provide a code (e.g. IPCA) or --all", file=sys.stderr)
        return 2
    if args.all and args.code:
        print("collect: --all and a code are mutually exclusive", file=sys.stderr)
        return 2
    target = "--all" if args.all else args.code
    return _not_implemented(f"collect {target}")


def cmd_backfill(args: argparse.Namespace) -> int:
    return _not_implemented(f"backfill {args.code}")


def cmd_build(args: argparse.Namespace) -> int:
    return _not_implemented("build")


def cmd_deploy(args: argparse.Namespace) -> int:
    return _not_implemented("deploy")


def cmd_publish(args: argparse.Namespace) -> int:
    return _not_implemented("publish")


def cmd_status(args: argparse.Namespace) -> int:
    db_path = REPO_ROOT / "data" / "indicadores.db"
    site_data = REPO_ROOT / "site" / "data"
    site_charts = REPO_ROOT / "site" / "public" / "charts"

    print(f"indicadores-economicos pipeline v{VERSION}")
    print(f"  repo root:   {REPO_ROOT}")
    print(f"  db path:     {db_path} ({'exists' if db_path.exists() else 'not created yet'})")
    print(f"  site data:   {site_data} ({'exists' if site_data.exists() else 'not created yet'})")
    print(f"  site charts: {site_charts} ({'exists' if site_charts.exists() else 'not created yet'})")
    print("  indicators:  none registered yet (run migrations in M1)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="Pipeline de coleta e build dos indicadores econômicos.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("migrate", help="Aplica migrations pendentes").set_defaults(func=cmd_migrate)

    p_collect = sub.add_parser("collect", help="Coleta indicadores")
    p_collect.add_argument("code", nargs="?", help="Código de um indicador específico (ex: IPCA)")
    p_collect.add_argument("--all", action="store_true", help="Roda scheduler em todos os indicadores ativos")
    p_collect.set_defaults(func=cmd_collect)

    p_backfill = sub.add_parser("backfill", help="Coleta histórico inteiro de um indicador")
    p_backfill.add_argument("code", help="Código do indicador (ex: IPCA)")
    p_backfill.set_defaults(func=cmd_backfill)

    sub.add_parser("build", help="Gera JSONs + PNGs").set_defaults(func=cmd_build)
    sub.add_parser("deploy", help="git add + commit + push").set_defaults(func=cmd_deploy)
    sub.add_parser("publish", help="build + deploy").set_defaults(func=cmd_publish)
    sub.add_parser("status", help="Resumo do pipeline").set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
