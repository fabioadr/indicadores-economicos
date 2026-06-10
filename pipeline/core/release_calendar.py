"""Calendário de divulgação — datas oficiais (IBGE) + estimativa.

Estratégia híbrida:
  - Indicadores do IBGE (IPCA, INPC, IPCA-15) têm datas oficiais na API de
    calendário do IBGE; são buscadas na coleta e persistidas em `release_dates`.
  - Demais indicadores (FGV: IGP-M/DI, INCC-M; BCB: SELIC/CDI/TR/SELICAC) usam
    estimativa calculada a partir de `expected_release_day` + frequência.

Separação do projeto: rede roda na coleta (`refresh_official_dates`); o build é
puro a partir do DB e calcula a estimativa quando não há data oficial.
"""

from __future__ import annotations

import calendar
import logging
import sqlite3
from dataclasses import dataclass
from datetime import date

import httpx
from dateutil.relativedelta import relativedelta

from pipeline.db.connection import (
    Indicator,
    get_indicator_by_code,
    upsert_release_date,
)

logger = logging.getLogger(__name__)

IBGE_CALENDAR_URL = "https://servicodados.ibge.gov.br/api/v3/calendario"
HTTP_TIMEOUT_SECONDS = 30.0
LOOKAHEAD_MONTHS = 6

# Indicadores cobertos pela API de calendário do IBGE.
IBGE_CODES = ("IPCA", "INPC", "IPCA15")


@dataclass
class ReleaseEntry:
    code: str
    release_date: date
    title: str | None = None
    reference_period: str | None = None


def _match_code(nome_produto: str | None, alias_produto: str | None) -> str | None:
    """Mapeia um item do calendário IBGE para o `code` de um indicador nosso."""
    nome = (nome_produto or "").lower()
    alias = (alias_produto or "").lower()

    # IPCA-15 antes de IPCA (ambos contêm "amplo").
    if "15" in nome or "15" in alias:
        if "ipca" in nome or "ipca" in alias or "amplo" in nome:
            return "IPCA15"
        return None
    if "ipca" in alias or "amplo" in nome:
        return "IPCA"
    if "inpc" in alias or (
        "nacional de pre" in nome and "consumidor" in nome and "amplo" not in nome
    ):
        return "INPC"
    return None


def _parse_release_date(value: str) -> date | None:
    """Parseia "DD/MM/YYYY HH:MM:SS" (ou só a data) para `date`."""
    try:
        d, m, y = value.strip()[:10].split("/")
        return date(int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return None


def fetch_ibge_calendar(since: date, until: date) -> list[ReleaseEntry]:
    """Busca divulgações no calendário do IBGE entre `since` e `until`.

    Retorna apenas itens mapeáveis para indicadores cobertos (IBGE_CODES).
    Levanta httpx.HTTPError em falha de rede; o caller decide se contém.
    """
    params = {
        "de": since.isoformat(),
        "ate": until.isoformat(),
        "qtd": 100,
    }
    response = httpx.get(
        IBGE_CALENDAR_URL, params=params, timeout=HTTP_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    data = response.json()
    items = data.get("items", []) if isinstance(data, dict) else data

    entries: list[ReleaseEntry] = []
    for item in items or []:
        code = _match_code(item.get("nome_produto"), item.get("alias_produto"))
        if code is None:
            continue
        rdate = _parse_release_date(item.get("data_divulgacao", ""))
        if rdate is None:
            continue
        ref = None
        ano = item.get("ano_referencia_fim") or item.get("ano_referencia_inicio")
        mes = item.get("mes_referencia_fim") or item.get("mes_referencia_inicio")
        if ano and mes:
            ref = f"{int(ano):04d}-{int(mes):02d}"
        entries.append(
            ReleaseEntry(
                code=code,
                release_date=rdate,
                title=item.get("titulo"),
                reference_period=ref,
            )
        )
    return entries


def refresh_official_dates(
    conn: sqlite3.Connection, today: date | None = None
) -> list[ReleaseEntry]:
    """Coleta e persiste datas oficiais futuras do IBGE. Fail-soft.

    Erros de rede são logados e contidos (retorna lista vazia) para nunca
    derrubar a coleta. Retorna as entradas efetivamente persistidas.
    """
    today = today or date.today()
    until = today + relativedelta(months=LOOKAHEAD_MONTHS)
    try:
        entries = fetch_ibge_calendar(today, until)
    except Exception as exc:  # noqa: BLE001 — fail-loud no log, mas não derruba
        logger.warning("refresh_official_dates: falha ao buscar calendário IBGE: %s", exc)
        return []

    persisted: list[ReleaseEntry] = []
    for entry in entries:
        if entry.release_date < today:
            continue
        indicator = get_indicator_by_code(conn, entry.code)
        if indicator is None or not indicator.active:
            continue
        upsert_release_date(
            conn,
            indicator.id,
            release_date=entry.release_date.isoformat(),
            source="ibge",
            reference_period=entry.reference_period,
            title=entry.title,
        )
        persisted.append(entry)

    logger.info("refresh_official_dates: %d datas oficiais persistidas", len(persisted))
    return persisted


def _safe_date(year: int, month: int, day: int) -> date:
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last))


def estimated_next_release(
    indicator: Indicator,
    latest_reference_date: date | None,
    today: date,
) -> date:
    """Estima a próxima divulgação a partir de `expected_release_day`.

    Regra (mensais): a última referência já está publicada, então a próxima
    divulgação corresponde à referência seguinte (+1 mês), publicada ~2 meses
    após a última referência, no dia `expected_release_day`. Rola para frente
    enquanto a data candidata for anterior a hoje.
    """
    day = indicator.expected_release_day or 1
    if latest_reference_date is None:
        candidate = _safe_date(today.year, today.month, day)
    else:
        base = latest_reference_date + relativedelta(months=2)
        candidate = _safe_date(base.year, base.month, day)
    while candidate < today:
        nxt = candidate + relativedelta(months=1)
        candidate = _safe_date(nxt.year, nxt.month, day)
    return candidate


def next_release_for(
    indicator: Indicator,
    official_dates: dict[str, date],
    latest_reference_date: date | None,
    today: date,
) -> dict:
    """Retorna {"date": ISO, "source": "official"|"estimated"} para o indicador."""
    official = official_dates.get(indicator.id)
    if official is not None:
        return {"date": official.isoformat(), "source": "official"}
    est = estimated_next_release(indicator, latest_reference_date, today)
    return {"date": est.isoformat(), "source": "estimated"}
