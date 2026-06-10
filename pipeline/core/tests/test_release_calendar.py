"""Tests for release_calendar: matching, date parse, estimativa, next_release."""

from __future__ import annotations

from datetime import date

from pipeline.core import release_calendar as rc
from pipeline.db.connection import Indicator


def _ind(code="IPCA", *, expected_release_day=10, frequency="monthly") -> Indicator:
    return Indicator(
        id=f"id-{code}",
        code=code,
        slug=code.lower(),
        name=code,
        category="inflacao",
        frequency=frequency,
        connector_type="bcb_sgs",
        connector_config="{}",
        inception_date=date(2000, 1, 1),
        expected_release_day=expected_release_day,
        active=True,
        last_collected_at=None,
    )


def test_match_code_distinguishes_ipca_variants():
    assert rc._match_code("Índice Nacional de Preços ao Consumidor Amplo", "ipca") == "IPCA"
    assert rc._match_code("Índice Nacional de Preços ao Consumidor Amplo 15", "ipca15") == "IPCA15"
    assert rc._match_code("Índice Nacional de Preços ao Consumidor", "inpc") == "INPC"
    # Produtos não cobertos não casam.
    assert rc._match_code("Pesquisa Nacional por Amostra de Domicílios", "pnadc") is None


def test_parse_release_date():
    assert rc._parse_release_date("11/07/2026 09:00:00") == date(2026, 7, 11)
    assert rc._parse_release_date("01/12/2026") == date(2026, 12, 1)
    assert rc._parse_release_date("lixo") is None


def test_estimated_next_release_two_months_after_reference():
    ind = _ind(expected_release_day=10)
    # Última referência abril → próxima divulgação ~junho dia 10.
    got = rc.estimated_next_release(ind, date(2026, 4, 1), today=date(2026, 5, 20))
    assert got == date(2026, 6, 10)


def test_estimated_next_release_rolls_forward_when_past():
    ind = _ind(expected_release_day=10)
    # Candidata (jun/10) já passou em hoje=jul/01 → rola para jul/10.
    got = rc.estimated_next_release(ind, date(2026, 4, 1), today=date(2026, 7, 1))
    assert got == date(2026, 7, 10)


def test_estimated_next_release_clamps_day_to_month_length():
    ind = _ind(expected_release_day=31)
    # base = dez/2025 + 2 = fev/2026; dia 31 → clamp 28.
    got = rc.estimated_next_release(ind, date(2025, 12, 1), today=date(2026, 1, 1))
    assert got == date(2026, 2, 28)


def test_next_release_prefers_official():
    ind = _ind()
    official = {ind.id: date(2026, 7, 11)}
    out = rc.next_release_for(ind, official, date(2026, 4, 1), today=date(2026, 6, 1))
    assert out == {"date": "2026-07-11", "source": "official"}


def test_next_release_falls_back_to_estimate():
    ind = _ind(expected_release_day=10)
    out = rc.next_release_for(ind, {}, date(2026, 4, 1), today=date(2026, 5, 20))
    assert out == {"date": "2026-06-10", "source": "estimated"}
