"""Pipeline CLI — entry point para collect, build, deploy, status, etc.

M1 implementou `migrate`. M4 plugou `collect` e `backfill`. Os demais comandos
ainda são stubs até seus milestones (M5: build, M9: deploy/publish).
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path

from pipeline import config
from pipeline.core import builder, scheduler
from pipeline.core.cron import is_cron_match, next_run
from pipeline.db.connection import (
    apply_pending_migrations,
    get_active_schedule,
    get_connection,
    get_indicator_by_code,
    get_last_successful_build,
    update_schedule_next_run,
    update_schedule_run,
)

logger = logging.getLogger(__name__)

VERSION = "0.0.1"


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


def _print_deploy(result: builder.DeployResult) -> None:
    if result.status == "no_changes":
        print("deploy: working tree limpo (nada para commitar)")
        return
    sha = (result.commit_sha or "")[:8]
    print(f"deploy: success ({sha}) — {len(result.files_changed)} arquivo(s)")


def _build_result_from_log(log) -> builder.BuildResult:
    codes = [c for c in (log.indicators_updated or "").split(",") if c]
    return builder.BuildResult(
        status="success",
        changed=codes,
        files_generated=log.files_generated or 0,
        log_id=log.id,
    )


def cmd_deploy(args: argparse.Namespace) -> int:
    _ensure_db_ready()
    conn = get_connection(config.DB_PATH)
    try:
        last = get_last_successful_build(conn)
        if last is None:
            print(
                "deploy: nenhum build bem-sucedido no histórico — rode `pipeline build` primeiro.",
                file=sys.stderr,
            )
            return 2
        build_result = _build_result_from_log(last)
        try:
            result = builder.deploy(conn, build_result, triggered_by="cli")
        except Exception as exc:  # noqa: BLE001
            print(f"deploy: falhou ({type(exc).__name__}: {exc})", file=sys.stderr)
            return 1
        _print_deploy(result)
        return 0
    finally:
        conn.close()


def cmd_publish(args: argparse.Namespace) -> int:
    _ensure_db_ready()
    conn = get_connection(config.DB_PATH)
    try:
        try:
            build_result = builder.build(conn, triggered_by="cli")
        except Exception as exc:  # noqa: BLE001
            print(f"publish: build falhou ({type(exc).__name__}: {exc})", file=sys.stderr)
            return 1

        if build_result.status == "no_changes":
            print("publish: build sem mudanças — nada a deployar")
            return 0

        print(f"publish: build {build_result.status} ({build_result.files_generated} arquivos)")
        for code in build_result.changed:
            print(f"  rebuilt: {code}")

        try:
            deploy_result = builder.deploy(conn, build_result, triggered_by="cli")
        except Exception as exc:  # noqa: BLE001
            print(f"publish: deploy falhou ({type(exc).__name__}: {exc})", file=sys.stderr)
            return 1
        _print_deploy(deploy_result)
        return 0
    finally:
        conn.close()


def cmd_scheduled_collect(args: argparse.Namespace) -> int:
    _ensure_db_ready()
    conn = get_connection(config.DB_PATH)
    try:
        cfg = get_active_schedule(conn)
        if cfg is None or not cfg.enabled:
            logger.debug("scheduled-collect: skip — %s", "no schedule" if cfg is None else "paused")
            return 0

        now = datetime.now()
        try:
            match = is_cron_match(cfg.cron_expression, now)
        except Exception as exc:  # noqa: BLE001
            logger.error("scheduled-collect: invalid cron expression %r: %s", cfg.cron_expression, exc)
            return 1

        if not match:
            logger.debug("scheduled-collect: skip — out of window (%s)", cfg.cron_expression)
            return 0

        logger.info("scheduled-collect: running collect (cron=%s)", cfg.cron_expression)
        results = scheduler.run_all(conn, triggered_by="cron")

        has_changes = any(r.added or r.updated for r in results)
        if has_changes:
            try:
                build_result = builder.build(conn, triggered_by="cron")
            except Exception as exc:  # noqa: BLE001
                logger.error("scheduled-collect: build failed: %s", exc)
                update_schedule_run(conn, cfg.id, now.isoformat())
                return 1

            if build_result.status == "success":
                try:
                    builder.deploy(conn, build_result, triggered_by="cron")
                except Exception as exc:  # noqa: BLE001
                    logger.error("scheduled-collect: deploy failed: %s", exc)
                    update_schedule_run(conn, cfg.id, now.isoformat())
                    return 1

        update_schedule_run(conn, cfg.id, now.isoformat())
        try:
            nr = next_run(cfg.cron_expression, now)
            update_schedule_next_run(conn, cfg.id, nr.isoformat())
        except Exception as exc:  # noqa: BLE001
            logger.warning("scheduled-collect: could not compute next_run: %s", exc)

        return 0
    finally:
        conn.close()


def cmd_calendar_refresh(args: argparse.Namespace) -> int:
    from datetime import date

    from pipeline.core import release_calendar

    _ensure_db_ready()
    conn = get_connection(config.DB_PATH)
    try:
        persisted = release_calendar.refresh_official_dates(conn, date.today())
    finally:
        conn.close()

    if not persisted:
        print("calendar-refresh: nenhuma data oficial nova")
        return 0
    for entry in sorted(persisted, key=lambda e: e.release_date):
        print(f"  {entry.code}: {entry.release_date.isoformat()}")
    return 0


def _gsc_config_or_exit() -> tuple[str, Path]:
    site = config.GSC_SITE_URL
    creds = config.GSC_CREDENTIALS_PATH
    if not site:
        print("gsc: GSC_SITE_URL ausente. Ver docs/gsc/SETUP.md.", file=sys.stderr)
        raise SystemExit(2)
    if not Path(creds).exists():
        print(
            f"gsc: credenciais não encontradas em {creds}. Ver docs/gsc/SETUP.md.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return site, creds


def cmd_gsc_sites(args: argparse.Namespace) -> int:
    from pipeline.gsc.client import GscClient
    from pipeline.gsc.exceptions import GscError

    site, creds = _gsc_config_or_exit()
    try:
        with GscClient(site, credentials_path=creds) as client:
            entries = client.list_sites()
    except GscError as exc:
        print(f"gsc-sites: {exc}", file=sys.stderr)
        return 1
    if not entries:
        print("gsc-sites: nenhuma propriedade visível para esta service account")
        print("  → adicione o client_email como usuário no GSC (docs/gsc/SETUP.md)")
        return 1
    print(f"gsc-sites: {len(entries)} propriedade(s)")
    for entry in entries:
        mark = " ← GSC_SITE_URL" if entry.site_url == site else ""
        print(f"  {entry.site_url}  ({entry.permission_level}){mark}")
    if site not in {e.site_url for e in entries}:
        print(
            f"aviso: GSC_SITE_URL={site!r} não está na lista — confira o valor exato.",
            file=sys.stderr,
        )
        return 1
    return 0


def cmd_gsc_collect(args: argparse.Namespace) -> int:
    from pipeline.bot import notifications
    from pipeline.gsc.client import GscClient
    from pipeline.gsc.collect import collect
    from pipeline.gsc.exceptions import GscError

    _ensure_db_ready()
    site, creds = _gsc_config_or_exit()
    since = date.fromisoformat(args.since) if args.since else None
    until = date.fromisoformat(args.until) if args.until else None
    conn = get_connection(config.DB_PATH)
    try:
        with GscClient(site, credentials_path=creds) as client:
            result = collect(
                conn,
                client,
                backfill=args.backfill,
                since=since,
                triggered_by="cli",
                until=until,
            )
    except GscError as exc:
        notifications.send_gsc_collect_error(str(exc))
        print(f"gsc-collect: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()

    if not result.ok:
        notifications.send_gsc_collect_error(result.error or "erro desconhecido")
        print(f"gsc-collect: {result.error}", file=sys.stderr)
        return 1

    start = result.start.isoformat() if result.start else "—"
    end = result.end.isoformat() if result.end else "—"
    print(
        f"gsc-collect: {start} → {end}  "
        f"days_ok={result.days_ok} empty={result.days_empty} "
        f"rows={result.rows_upserted} appearance={result.appearance_rows}"
    )
    if args.notify:
        notifications.send_gsc_collect_success(result)
    return 0


def cmd_gsc_report(args: argparse.Namespace) -> int:
    from pipeline.bot import notifications
    from pipeline.gsc.report import build_briefing

    _ensure_db_ready()
    conn = get_connection(config.DB_PATH)
    try:
        briefing = build_briefing(conn, days=args.days)
    finally:
        conn.close()

    from pipeline.bot import formatters

    text = formatters.gsc_report_message(briefing)
    # stdout sem tags HTML para leitura no terminal
    print(text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", ""))
    notifications.send_gsc_report(briefing)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    creds_ok = config.GSC_CREDENTIALS_PATH.exists()
    print(f"indicadores-economicos pipeline v{VERSION}")
    print(f"  repo root:   {config.REPO_ROOT}")
    print(f"  db path:     {config.DB_PATH} ({'exists' if config.DB_PATH.exists() else 'not created yet'})")
    print(f"  site data:   {config.SITE_DATA_DIR} ({'exists' if config.SITE_DATA_DIR.exists() else 'not created yet'})")
    print(f"  site charts: {config.SITE_CHARTS_DIR} ({'exists' if config.SITE_CHARTS_DIR.exists() else 'not created yet'})")
    print(f"  gsc site:    {config.GSC_SITE_URL or '(GSC_SITE_URL não definido)'}")
    print(f"  gsc creds:   {config.GSC_CREDENTIALS_PATH} ({'exists' if creds_ok else 'missing'})")
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

    sub.add_parser(
        "calendar-refresh",
        help="Atualiza datas oficiais de divulgação (calendário IBGE)",
    ).set_defaults(func=cmd_calendar_refresh)
    sub.add_parser("build", help="Gera JSONs + PNGs").set_defaults(func=cmd_build)
    sub.add_parser("deploy", help="git add + commit + push").set_defaults(func=cmd_deploy)
    sub.add_parser("publish", help="build + deploy").set_defaults(func=cmd_publish)
    sub.add_parser("status", help="Resumo do pipeline").set_defaults(func=cmd_status)
    sub.add_parser(
        "scheduled-collect",
        help="Coleta automática via cron — executa apenas se a hora bater com a config do DB",
    ).set_defaults(func=cmd_scheduled_collect)

    sub.add_parser(
        "gsc-sites",
        help="Lista propriedades GSC visíveis para a service account (smoke de acesso)",
    ).set_defaults(func=cmd_gsc_sites)

    p_gsc_collect = sub.add_parser(
        "gsc-collect",
        help="Coleta Search Console (dia a dia) para o SQLite local",
    )
    p_gsc_collect.add_argument(
        "--backfill",
        action="store_true",
        help="Puxa 16 meses (primeira carga). Sem isto, últimos ~7 dias.",
    )
    p_gsc_collect.add_argument("--since", help="Início YYYY-MM-DD (inclusive)")
    p_gsc_collect.add_argument("--until", help="Fim YYYY-MM-DD (inclusive)")
    p_gsc_collect.add_argument(
        "--notify",
        action="store_true",
        help="Envia resumo de sucesso no Telegram (erro sempre notifica)",
    )
    p_gsc_collect.set_defaults(func=cmd_gsc_collect)

    p_gsc_report = sub.add_parser(
        "gsc-report",
        help="Briefing semanal GSC (Telegram + stdout)",
    )
    p_gsc_report.add_argument(
        "--days",
        type=int,
        default=7,
        help="Tamanho da janela em dias (padrão 7)",
    )
    p_gsc_report.set_defaults(func=cmd_gsc_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    config.setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
