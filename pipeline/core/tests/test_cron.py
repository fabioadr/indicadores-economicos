"""Testes para pipeline.core.cron."""

from __future__ import annotations

from datetime import datetime

import pytest

from pipeline.core.cron import is_cron_match, next_run, validate_frequency


class TestIsCronMatch:
    def test_matches_within_hour(self):
        # 07:00 diário; verificar com 07:30 (dentro da hora das 7)
        dt = datetime(2026, 5, 6, 7, 30)
        assert is_cron_match("0 7 * * *", dt) is True

    def test_matches_at_exact_hour_boundary(self):
        # dt = 07:00:00 exato
        dt = datetime(2026, 5, 6, 7, 0, 0)
        assert is_cron_match("0 7 * * *", dt) is True

    def test_no_match_different_hour(self):
        dt = datetime(2026, 5, 6, 8, 30)
        assert is_cron_match("0 7 * * *", dt) is False

    def test_no_match_one_hour_past(self):
        # expressão 07:00; verificar com 08:00 (próxima seria 07:00 do dia seguinte)
        dt = datetime(2026, 5, 6, 8, 0)
        assert is_cron_match("0 7 * * *", dt) is False

    def test_matches_any_hour(self):
        # "@hourly" equivalente: 0 * * * *
        dt = datetime(2026, 5, 6, 14, 15)
        assert is_cron_match("0 * * * *", dt) is True

    def test_matches_two_times_per_day(self):
        # 0 8,18 * * * — bate às 8h e 18h
        dt_8 = datetime(2026, 5, 6, 8, 0)
        dt_18 = datetime(2026, 5, 6, 18, 0)
        dt_12 = datetime(2026, 5, 6, 12, 0)
        assert is_cron_match("0 8,18 * * *", dt_8) is True
        assert is_cron_match("0 8,18 * * *", dt_18) is True
        assert is_cron_match("0 8,18 * * *", dt_12) is False

    def test_invalid_expression_raises(self):
        with pytest.raises(Exception):
            is_cron_match("not a cron", datetime.now())


class TestValidateFrequency:
    def test_valid_literal_minute(self):
        assert validate_frequency("0 7 * * *") is True
        assert validate_frequency("30 8 * * *") is True
        assert validate_frequency("15 9 * * 1-5") is True

    def test_rejects_star_in_minutes(self):
        assert validate_frequency("* * * * *") is False

    def test_rejects_step_in_minutes(self):
        assert validate_frequency("*/15 * * * *") is False
        assert validate_frequency("*/1 * * * *") is False

    def test_rejects_list_in_minutes(self):
        assert validate_frequency("0,30 * * * *") is False

    def test_rejects_range_in_minutes(self):
        assert validate_frequency("0-5 * * * *") is False

    def test_empty_expression(self):
        assert validate_frequency("") is False


class TestNextRun:
    def test_next_run_basic(self):
        dt = datetime(2026, 5, 6, 7, 0)
        result = next_run("0 7 * * *", dt)
        assert result == datetime(2026, 5, 7, 7, 0)

    def test_next_run_type(self):
        result = next_run("0 7 * * *", datetime(2026, 5, 6, 7, 0))
        assert isinstance(result, datetime)
