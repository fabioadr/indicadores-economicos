"""Templates de mensagem do bot (puro: não faz I/O).

Cada função recebe os dados já carregados e devolve uma string pronta para
o Telegram (parse_mode=HTML — escape feito aqui).
"""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline.core.builder import BuildResult, DeployResult
    from pipeline.core.scheduler import CollectResult
    from pipeline.db.connection import (
        BuildLog,
        CollectionLog,
        Indicator,
        IndicatorValue,
    )

SITE_URL = "https://indicadoreseconomicoshoje.com.br/"

CATEGORY_ICON = {
    "inflacao": "🏛",
    "juros": "💰",
    "correcao_monetaria": "🏠",
}

_PT_MONTHS = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
    7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
}


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}".replace(".", ",") + "%"


def _fmt_month(d) -> str:
    return f"{_PT_MONTHS[d.month]}/{d.year}"


def _fmt_iso_local(ts: str | None) -> str:
    if not ts:
        return "—"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%d/%m %H:%M")
    except ValueError:
        return ts


def help_message() -> str:
    return (
        "<b>Indicadores Econômicos Hoje</b>\n\n"
        "Comandos disponíveis:\n"
        "/status — resumo do sistema\n"
        "/indicadores — lista indicadores ativos\n"
        "/coletar &lt;CODE|all&gt; — roda coleta imediata\n"
        "/publicar — gera build + deploy\n"
        "/logs [n] — últimas n entradas do log\n"
        "/erros — erros das últimas 24h\n"
        "/help — esta mensagem"
    )


def status_message(
    *,
    active_count: int,
    last_build: "BuildLog | None",
    errors_24h: int,
) -> str:
    if last_build and last_build.finished_at:
        last_build_str = _fmt_iso_local(last_build.finished_at)
        updated = last_build.indicators_updated or ""
        n_updates = len([c for c in updated.split(",") if c]) if updated else 0
        deploy_line = f"Último deploy: {last_build_str} (com {n_updates} atualizações)"
    else:
        deploy_line = "Último deploy: —"

    return (
        "📊 <b>Indicadores Econômicos Hoje</b>\n\n"
        f"Indicadores ativos: {active_count}\n"
        f"{deploy_line}\n\n"
        f"Erros nas últimas 24h: {errors_24h}"
    )


def indicators_message(
    indicators: list["Indicator"],
    latest_by_id: dict[str, "IndicatorValue | None"],
) -> str:
    if not indicators:
        return "📋 Nenhum indicador ativo."

    lines = ["📋 <b>Indicadores ativos</b>", ""]
    for ind in indicators:
        icon = CATEGORY_ICON.get(ind.category, "📈")
        latest = latest_by_id.get(ind.id)
        last_collect = _fmt_iso_local(ind.last_collected_at)
        lines.append(f"{icon} <b>{escape(ind.code)}</b> ({ind.frequency})")
        lines.append(f"   Última coleta: {last_collect}")
        if latest is not None:
            lines.append(
                f"   Último valor: {_fmt_pct(latest.value)} ({_fmt_month(latest.reference_date)})"
            )
        else:
            lines.append("   Último valor: —")
        lines.append("")
    return "\n".join(lines).rstrip()


def collect_starting_message(code: str) -> str:
    return f"🔄 Coletando {escape(code)}..."


def collect_result_message(result: "CollectResult", latest: "IndicatorValue | None") -> str:
    if not result.ok:
        return (
            f"❌ <b>Erro na coleta</b>\n\n"
            f"Indicador: {escape(result.code)}\n"
            f"Erro: {escape(result.error or '')}"
        )
    if result.added == 0 and result.updated == 0:
        return (
            f"✅ <b>{escape(result.code)}</b> já está atualizado.\n"
            f"Nenhum valor novo."
        )
    parts = [f"✅ <b>{escape(result.code)}</b> coletado"]
    if result.added:
        parts.append(f"   {result.added} valor(es) novo(s)")
        if latest is not None:
            parts.append(
                f"   Último: {_fmt_pct(latest.value)} ({_fmt_month(latest.reference_date)})"
            )
    if result.updated:
        parts.append(f"   {result.updated} valor(es) atualizado(s)")
    parts.append("   Recalculou agregações.")
    parts.append("   Pronto para publicar com /publicar.")
    return "\n".join(parts)


def collect_summary_message(results: list["CollectResult"]) -> str:
    if not results:
        return "ℹ️ Nada a coletar."
    lines = ["📥 <b>Coleta concluída</b>", ""]
    any_change = False
    any_error = False
    for r in results:
        if r.ok:
            if r.added or r.updated:
                lines.append(
                    f"• {escape(r.code)}: +{r.added} novo(s), {r.updated} atualizado(s)"
                )
                any_change = True
            else:
                lines.append(f"• {escape(r.code)}: sem mudanças")
        else:
            lines.append(f"• {escape(r.code)}: ❌ {escape(r.error or '')}")
            any_error = True
    if any_change:
        lines.append("")
        lines.append("Use /publicar para gerar o build.")
    if any_error:
        lines.append("")
        lines.append("⚠️ Houve erros — confira /erros.")
    return "\n".join(lines)


def collect_error_message(indicator: "Indicator", error: str) -> str:
    now = datetime.now(tz=timezone.utc).strftime("%d/%m %H:%M UTC")
    return (
        "❌ <b>ERRO na coleta</b>\n\n"
        f"Indicador: {escape(indicator.code)}\n"
        f"Hora: {now}\n"
        f"Erro: {escape(error)}\n\n"
        f"Tente novamente com /coletar {escape(indicator.code)}"
    )


def build_success_message(result: "BuildResult") -> str:
    codes = ", ".join(escape(c) for c in result.changed)
    return (
        "🛠 <b>Build concluído</b>\n\n"
        f"Indicadores atualizados: {codes}\n"
        f"Arquivos gerados: {result.files_generated}"
    )


def build_error_message(exc: BaseException) -> str:
    return (
        "❌ <b>ERRO no build</b>\n\n"
        f"{escape(type(exc).__name__)}: {escape(str(exc))}"
    )


def deploy_success_message(
    deploy_result: "DeployResult", build_result: "BuildResult"
) -> str:
    codes = ", ".join(escape(c) for c in build_result.changed) or "—"
    sha = (deploy_result.commit_sha or "")[:7]
    sha_line = f"Commit: <code>{escape(sha)}</code>\n" if sha else ""
    return (
        "🚀 <b>Deploy concluído</b>\n\n"
        f"Indicadores: {codes}\n"
        f"{sha_line}"
        f"{escape(SITE_URL)}\n\n"
        "Vercel detecta o push em ~1–2min."
    )


def deploy_error_message(exc: BaseException) -> str:
    return (
        "❌ <b>ERRO no deploy</b>\n\n"
        f"{escape(type(exc).__name__)}: {escape(str(exc))}"
    )


def publish_summary_message(
    build_result: "BuildResult", deploy_result: "DeployResult | None"
) -> str:
    if build_result.status == "no_changes":
        return "ℹ️ Nenhum indicador precisava de rebuild."
    if deploy_result is None or deploy_result.status == "no_changes":
        codes = ", ".join(escape(c) for c in build_result.changed) or "—"
        return (
            "🛠 <b>Build concluído</b>\n\n"
            f"Indicadores atualizados: {codes}\n"
            f"Arquivos gerados: {build_result.files_generated}\n\n"
            "ℹ️ Working tree limpo — nada para commitar."
        )
    return deploy_success_message(deploy_result, build_result)


def logs_message(logs: list["CollectionLog"]) -> str:
    if not logs:
        return "📭 Sem logs ainda."
    lines = [f"📜 <b>Últimos {len(logs)} eventos</b>", ""]
    for log in logs:
        when = _fmt_iso_local(log.started_at)
        code = log.indicator_code or "—"
        if log.status == "success":
            tag = f"✅ +{log.records_added}/{log.records_updated}"
        elif log.status == "skipped":
            tag = "⏭ skip"
        elif log.status == "running":
            tag = "⏳ rodando"
        else:
            tag = f"❌ {(log.error_message or '').split(chr(10))[0][:80]}"
        lines.append(f"{when} {escape(code)} ({log.triggered_by}) — {escape(tag)}")
    return "\n".join(lines)


def errors_message(logs: list["CollectionLog"]) -> str:
    if not logs:
        return "✅ Sem erros nas últimas 24h."
    lines = [f"⚠️ <b>{len(logs)} erro(s) nas últimas 24h</b>", ""]
    for log in logs:
        when = _fmt_iso_local(log.started_at)
        code = log.indicator_code or "—"
        msg = (log.error_message or "").split("\n")[0][:200]
        lines.append(f"{when} {escape(code)}: {escape(msg)}")
    return "\n".join(lines)


def unauthorized_message() -> str:
    return "⛔ Não autorizado."
