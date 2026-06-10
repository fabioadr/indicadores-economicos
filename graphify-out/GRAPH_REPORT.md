# Graph Report - indicadores-economicos  (2026-06-10)

## Corpus Check
- 54 files · ~51,895 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 563 nodes · 1095 edges · 25 communities detected
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 290 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 31|Community 31]]

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 32 edges
2. `IBGESIDRAConnector` - 23 edges
3. `recompute_aggregations()` - 19 edges
4. `BCBSGSConnector` - 19 edges
5. `execute()` - 18 edges
6. `get_active_schedule()` - 18 edges
7. `apply_pending_migrations()` - 18 edges
8. `build()` - 17 edges
9. `list_values()` - 17 edges
10. `RawDataPoint` - 17 edges

## Surprising Connections (you probably didn't know these)
- `collect_starting_message()` --calls--> `escape()`  [INFERRED]
  pipeline/bot/formatters.py → site/src/lib/markdown.ts
- `collect_summary_message()` --calls--> `escape()`  [INFERRED]
  pipeline/bot/formatters.py → site/src/lib/markdown.ts
- `collect_error_message()` --calls--> `escape()`  [INFERRED]
  pipeline/bot/formatters.py → site/src/lib/markdown.ts
- `build_success_message()` --calls--> `escape()`  [INFERRED]
  pipeline/bot/formatters.py → site/src/lib/markdown.ts
- `build_error_message()` --calls--> `escape()`  [INFERRED]
  pipeline/bot/formatters.py → site/src/lib/markdown.ts

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (51): ABC, BaseConnector, BaseConnector, ConnectorError, FetchError, get_connector(), ParseError, Base interfaces for data source connectors.  Every external source (BCB, IBGE, F (+43 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (38): _apply_pending_migrations(), build_application(), main(), Entry point: `python -m pipeline.bot`.  Inicia long polling do Telegram com os h, Aplica migrations pendentes no startup do bot.      Sem isto, indicadores novos, apply_pending_migrations(), executescript(), get_active_schedule() (+30 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (43): _get_aggregation_mode(), backfill_indicator(), collect_single(), _has_value_for_month(), _next_since(), _parse_iso_datetime(), Coleta orquestrada — decide o que rodar e dispara conector + persistência.  Spec, Replica a regra documentada em docs/05-pipeline.md.      `conn` só é necessário (+35 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (17): is_cron_match(), next_run(), Utilitários puros de cron para o gatekeeper `scheduled-collect` e validação no b, True se há alguma execução agendada dentro da janela [hora_de(dt), +1h).      Co, False se o campo de minutos permite mais de 1 execução por hora.      Heurística, Próxima execução da expressão a partir de `dt`., validate_frequency(), cmd_scheduled_collect() (+9 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (37): Normalized point returned by any connector., RawDataPoint, accumulate(), _compound_updates(), _null_aggregations(), _propagate_monthly_to_all(), Recompute YTD / last_12m / last_24m / since_inception for an indicator.  Spec: d, Para o modo daily_to_monthly: cada valor diário herda as agregações do     seu ( (+29 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (30): build_groups_payload(), _find_latest_common_date(), generate_comparison_chart(), PNGs comparativos entre indicadores e payload de `site/data/groups.json`.  Spec:, Mínimo dos máximos de reference_date entre os indicadores do grupo,     consider, Pega o IndicatorValue mais recente com reference_date <= target., Monta o dict serializável para `site/data/groups.json`., Retorna (Indicator, [(date, value), ...]) filtrado por métrica não-nula. (+22 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (30): build(), _build_categories(), _build_commit_message(), _compute_next_by_id(), _current_year(), deploy(), _groups_to_rebuild(), _latest_detail() (+22 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (19): BuildResult, DeployResult, CollectResult, _BuildLog, _Indicator, Tests for pipeline/bot/formatters: pure message templates., test_build_success_message(), test_collect_error_message_contains_code() (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (22): build_error_message(), build_success_message(), collect_error_message(), collect_result_message(), collect_starting_message(), collect_summary_message(), deploy_error_message(), deploy_success_message() (+14 more)

### Community 9 - "Community 9"
Cohesion: 0.18
Nodes (15): _git_calls_recorder(), Tests for the M5 builder: JSON shape, needs_rebuild logic, no_changes path., Seed 14 monthly values so YTD and last_12m are populated., _seed_ipca(), test_build_logs_recorded(), test_build_no_changes_keeps_existing_groups_json(), test_build_no_changes_skips_charts(), test_build_no_changes_still_ensures_groups_json() (+7 more)

### Community 10 - "Community 10"
Cohesion: 0.22
Nodes (16): cmd_agendamento(), cmd_agendar(), cmd_cancelar(), cmd_coletar(), cmd_erros(), cmd_help(), cmd_indicadores(), cmd_logs() (+8 more)

### Community 11 - "Community 11"
Cohesion: 0.21
Nodes (15): get_indicator_by_code(), _ind(), Tests for the scheduler (M4): should_collect, collect_single, run_all., Insere um indicador de teste limpo (sem colisão com os seeds da Fase 1).      Ap, _seed_indicator(), test_backfill_calls_connector_with_no_since(), test_collect_single_handles_fetch_error(), test_collect_single_idempotent_second_run() (+7 more)

### Community 12 - "Community 12"
Cohesion: 0.23
Nodes (14): build_parser(), _build_result_from_log(), cmd_backfill(), cmd_build(), cmd_calendar_refresh(), cmd_collect(), cmd_deploy(), cmd_migrate() (+6 more)

### Community 13 - "Community 13"
Cohesion: 0.17
Nodes (15): estimated_next_release(), fetch_ibge_calendar(), _match_code(), next_release_for(), _parse_release_date(), Calendário de divulgação — datas oficiais (IBGE) + estimativa.  Estratégia híbri, Coleta e persiste datas oficiais futuras do IBGE. Fail-soft.      Erros de rede, Estima a próxima divulgação a partir de `expected_release_day`.      Regra (mens (+7 more)

### Community 14 - "Community 14"
Cohesion: 0.23
Nodes (9): formatDateLong(), formatDateShort(), formatMonthShort(), formatMonthYear(), groupByYearDesc(), monthOf(), parseISO(), reduceToMonthly() (+1 more)

### Community 15 - "Community 15"
Cohesion: 0.29
Nodes (11): _accumulate_running(), _category_color(), generate_chart_current_year(), generate_chart_history(), _last_per_month(), Static PNG charts for indicator pages.  Spec: docs/05-pipeline.md (1200x600 @ 10, Monthly line + 12m cumulative line over the entire series.      Para ``aggregati, Mantém apenas o último valor de cada (ano, mês), preservando a ordem. (+3 more)

### Community 16 - "Community 16"
Cohesion: 0.27
Nodes (11): _make_daily_values(), _make_values(), Smoke tests for chart generation: produces valid PNG files., Multiple daily values per month, mimicking TR shape., test_current_year_chart_daily_to_monthly_writes_png(), test_current_year_chart_mode_none_writes_png(), test_current_year_chart_with_no_year_data(), test_current_year_chart_writes_png() (+3 more)

### Community 17 - "Community 17"
Cohesion: 0.31
Nodes (10): _credentials(), Push notifications enviadas pelo pipeline para o Telegram via Bot API.  Decisão, Resumo de uma rodada de coleta. Chamado pelo scheduler.run_all., send_build_error(), send_build_success(), send_collect_error(), send_collect_success(), send_deploy_error() (+2 more)

### Community 18 - "Community 18"
Cohesion: 0.31
Nodes (7): _ind(), Tests for release_calendar: matching, date parse, estimativa, next_release., test_estimated_next_release_clamps_day_to_month_length(), test_estimated_next_release_rolls_forward_when_past(), test_estimated_next_release_two_months_after_reference(), test_next_release_falls_back_to_estimate(), test_next_release_prefers_official()

### Community 19 - "Community 19"
Cohesion: 0.25
Nodes (1): Tests for pipeline/bot/notifications: httpx-based fail-quiet sends.

### Community 20 - "Community 20"
Cohesion: 0.6
Nodes (5): loadCalendar(), loadDetail(), loadGroups(), loadIndex(), readJson()

### Community 21 - "Community 21"
Cohesion: 0.53
Nodes (5): _fake_update(), Tests for pipeline/bot/auth: chat-id whitelist decorator., test_authorized_chat_passes(), test_missing_chat_id_blocks(), test_unauthorized_chat_replies_and_skips()

### Community 22 - "Community 22"
Cohesion: 0.4
Nodes (3): Pipeline configuration: paths, env loading, and logging setup.  Single import po, Configure root logger with stdout + daily file handler.      Idempotent: subsequ, setup_logging()

### Community 23 - "Community 23"
Cohesion: 0.67
Nodes (1): Decorator de autorização — whitelist single-user via TELEGRAM_CHAT_ID.

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Fetch data from the source.          Returns a list ordered by `reference_date`

## Knowledge Gaps
- **104 isolated node(s):** `Pipeline configuration: paths, env loading, and logging setup.  Single import po`, `Configure root logger with stdout + daily file handler.      Idempotent: subsequ`, `Pipeline CLI — entry point para collect, build, deploy, status, etc.  M1 impleme`, `Configuração dos grupos de comparação curados (Fase 2 / M14).  Cada grupo gera u`, `Rótulo PT-BR do eixo Y para uma métrica de IndicatorValue.` (+99 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 19`** (8 nodes): `test_notifications.py`, `Tests for pipeline/bot/notifications: httpx-based fail-quiet sends.`, `_reset_warning_flag()`, `test_send_message_noop_when_no_chat_id()`, `test_send_message_noop_when_no_token()`, `test_send_message_posts_to_bot_api()`, `test_send_message_swallows_http_errors()`, `test_send_message_swallows_network_errors()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (3 nodes): `authorized_only()`, `Decorator de autorização — whitelist single-user via TELEGRAM_CHAT_ID.`, `auth.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Fetch data from the source.          Returns a list ordered by `reference_date``
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RawDataPoint` connect `Community 4` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 9`?**
  _High betweenness centrality (0.185) - this node is a cross-community bridge._
- **Why does `cmd_scheduled_collect()` connect `Community 3` to `Community 1`, `Community 12`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `get_connection()` connect `Community 1` to `Community 2`, `Community 3`, `Community 12`, `Community 5`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `get_connection()` (e.g. with `cmd_migrate()` and `cmd_collect()`) actually correct?**
  _`get_connection()` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `IBGESIDRAConnector` (e.g. with `BaseConnector` and `FetchError`) actually correct?**
  _`IBGESIDRAConnector` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `recompute_aggregations()` (e.g. with `list_values()` and `batch_update_aggregations()`) actually correct?**
  _`recompute_aggregations()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `BCBSGSConnector` (e.g. with `BaseConnector` and `FetchError`) actually correct?**
  _`BCBSGSConnector` has 10 INFERRED edges - model-reasoned connections that need verification._