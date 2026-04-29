"""Pipeline CLI — entry point para collect, build, deploy, status, etc.

M1 implementou `migrate`. M4 plugou `collect` e `backfill`. Os demais comandos
ainda são stubs até seus milestones (M5: build, M9: deploy/publish).
"""

from __future__ import annotations

import argparse
import sys

from pipeline import config
from pipeline.core import builder, scheduler
from pipeline.db.connection import (
    apply_pending_migrations,
    get_connection,
    get_indicator_by_code,
)

VERSION = "0.0.1"


def _not_implemented(name: str) -> int:
    print(f"{name}: not implemented yet")
    return 0


def _ensure_db_ready() -> None:
    if not config.DB_PATH.exists():
        print(
            f"db not found at {config.DB_PATH}. Run `python -m pipeline.cli migrate` first.",
            file=sys.stderr,
        )
        sys.exit(2)


def cmd_migrate(args: argparse.Namespace) -> int:
    conn = get_connection(config.DB_PATH)
    try:
        applied = apply_pending_migrations(conn, config.MIGRATIONS_DIR)
    finally:
        conn.close()

    if not applied:
        print("no pending migrations")
    else:
        for name in applied:
            print(f"applied: {name}")
    return 0


def _print_results(results: list[scheduler.CollectResult]) -> int:
    if not results:
        print("nothing to collect")
        return 0
    exit_code = 0
    for r in results:
        status = "ok" if r.ok else f"ERROR ({r.error})"
        print(f"  {r.code}: added={r.added} updated={r.updated} {status}")
        if not r.ok:
            exit_code = 1
    return exit_code


def cmd_collect(args: argparse.Namespace) -> int:
    if not args.all and not args.code:
        print("collect: provide a code (e.g. IPCA) or --all", file=sys.stderr)
        return 2
    if args.all and args.code:
        print("collect: --all and a code are mutually exclusive", file=sys.stderr)
        return 2

    _ensure_db_ready()
    conn = get_connection(config.DB_PATH)
    try:
        if args.all:
            print("collect --all (running scheduler)")
            results = scheduler.run_all(conn, triggered_by="cli")
        else:
            indicator = get_indicator_by_code(conn, args.code)
            if indicator is None:
                print(f"collect: unknown indicator '{args.code}'", file=sys.stderr)
                return 2
            if not indicator.active:
                print(f"collect: indicator '{args.code}' is inactive", file=sys.stderr)
                return 2
            print(f"collect {indicator.code} (forced)")
            results = [scheduler.collect_single(conn, indicator, triggered_by="cli")]
        return _print_results(results)
    finally:
        conn.close()


def cmd_backfill(args: argparse.Namespace) -> int:
    _ensure_db_ready()
    conn = get_connection(config.DB_PATH)
    try:
        indicator = get_indicator_by_code(conn, args.code)
        if indicator is None:
            print(f"backfill: unknown indicator '{args.code}'", file=sys.stderr)
            return 2
        print(f"backfill {indicator.code} (this may take a few seconds)")
        result = scheduler.backfill_indicator(conn, indicator, triggered_by="backfill")
        return _print_results([result])
    finally:
        conn.close()


def cmd_build(args: argparse.Namespace) -> int:
    _ensure_db_ready()
    conn = get_connection(config.DB_PATH)
    try:
        result = builder.build(conn, triggered_by="cli")
    finally:
        conn.close()

    if result.status == "no_changes":
        print("build: no changes")
        return 0
    print(f"build: {result.status} ({result.files_generated} files)")
    for code in result.changed:
        print(f"  rebuilt: {code}")
    return 0 if result.status == "success" else 1


def cmd_deploy(args: argparse.Namespace) -> int:
    return _not_implemented("deploy")


def cmd_publish(args: argparse.Namespace) -> int:
    return _not_implemented("publish")


def cmd_status(args: argparse.Namespace) -> int:
    print(f"indicadores-economicos pipeline v{VERSION}")
    print(f"  repo root:   {config.REPO_ROOT}")
    print(f"  db path:     {config.DB_PATH} ({'exists' if config.DB_PATH.exists() else 'not created yet'})")
    print(f"  site data:   {config.SITE_DATA_DIR} ({'exists' if config.SITE_DATA_DIR.exists() else 'not created yet'})")
    print(f"  site charts: {config.SITE_CHARTS_DIR} ({'exists' if config.SITE_CHARTS_DIR.exists() else 'not created yet'})")
    print("  indicators:  run `sqlite3 data/indicadores.db 'SELECT code FROM indicators;'`")
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
    config.setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
