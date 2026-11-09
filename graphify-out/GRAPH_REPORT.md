# Graph Report - indicadores-economicos  (2026-11-09)

## Corpus Check
- 144 files · ~379,105 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 6, .sqlite 1, .db 1)

## Summary
- 1126 nodes · 2967 edges · 67 communities (38 shown, 29 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 97 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2da9dc0c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- datetime
- base.py
- builder.py
- get_connection
- test_aggregations.py
- connection.py
- test_ibge_sidra.py
- test_comparison_charts.py
- report.py
- scheduler.py
- package.json
- is_cron_match
- test_wage.py
- AGENTS.md
- notifications.py
- formatters.py
- format.ts
- IndicatorTableHistory.astro
- BaseLayout.astro
- [category]/index.astro
- test_formatters.py
- data.ts
- pages/[slug].astro
- handlers.py
- comparar/[slug].astro
- build_error_message
- DeployResult
- context7
- vercel.json
- tsconfig.json
- Astro Starter Kit: Minimal
- PeriodFilter.astro
- allowBuilds
- unauthorized_message
- precommit.sh
- validate-build.sh
- validate-fase2-build.sh
- inspect-db.sh
- install_cron.sh
- install_systemd.sh
- regenerate-comparisons.sh
- setup.sh
- validate-fase3-build.sh
- BCBSGSConnector
- IBGESIDRAConnector
- reproduce_bcb_fetch.py
- _fmt_iso_local
- test_notifications.py
- reproduce_sidra_fetch.py
- gsc_collect_error_message

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 64 edges
2. `build()` - 37 edges
3. `apply_pending_migrations()` - 33 edges
4. `Indicator` - 29 edges
5. `get_active_schedule()` - 28 edges
6. `list_values()` - 28 edges
7. `IBGESIDRAConnector` - 27 edges
8. `recompute_aggregations()` - 27 edges
9. `get_indicator_by_code()` - 26 edges
10. `cmd_scheduled_collect()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `Hooks (`.claude/settings.json`)` --references--> `deploy()`  [INFERRED]
  CLAUDE.md → pipeline/core/builder.py
- `7. Operação (como roda em produção)` --references--> `is_due()`  [INFERRED]
  AGENTS.md → pipeline/core/cron.py
- `5. Comandos` --references--> `deploy()`  [INFERRED]
  AGENTS.md → pipeline/core/builder.py
- `9. Não fazer` --references--> `build()`  [INFERRED]
  AGENTS.md → pipeline/core/builder.py
- `9. Não fazer` --references--> `deploy()`  [INFERRED]
  AGENTS.md → pipeline/core/builder.py

## Import Cycles
- None detected.

## Communities (67 total, 29 thin omitted)

### Community 0 - "datetime"
Cohesion: 0.06
Nodes (33): execute(), fetch_one(), fetch_access_token(), GscClient, GscRow, GscSite, collect(), _iter_days() (+25 more)

### Community 1 - "base.py"
Cohesion: 0.14
Nodes (8): BaseConnector, ConnectorError, FetchError, get_connector(), register(), _backoff(), _response_hint(), test_registry_resolves_ibge_sidra()

### Community 2 - "builder.py"
Cohesion: 0.05
Nodes (52): 10. Antes de dizer que terminou, 11. Workflows (runbooks), 12. graphify, 1. Regras de ambiente (leia antes de executar qualquer coisa), 2. O projeto, 3. Stack, 4. Estrutura, 5. Comandos (+44 more)

### Community 3 - "get_connection"
Cohesion: 0.07
Nodes (44): work_all(), work(), _auth_ok(), db_path(), build_parser(), _build_result_from_log(), cmd_backfill(), cmd_build() (+36 more)

### Community 4 - "test_aggregations.py"
Cohesion: 0.11
Nodes (29): accumulate(), _compound_updates(), _get_aggregation_mode(), _level_updates(), _null_aggregations(), pct_change(), _propagate_monthly_to_all(), recompute_aggregations() (+21 more)

### Community 5 - "connection.py"
Cohesion: 0.06
Nodes (64): authorized_only(), help_message(), cmd_agendamento(), work(), cmd_agendar(), work(), cmd_cancelar(), cmd_coletar() (+56 more)

### Community 6 - "test_ibge_sidra.py"
Cohesion: 0.18
Nodes (12): _load_fixture(), _no_pagination_pause(), test_dash_and_ellipsis_are_skipped(), test_empty_response_returns_empty_list(), test_http_404_raises_fetch_error(), test_http_500_raises_fetch_error(), test_malformed_json_raises_parse_error(), test_multiple_localities_are_filtered_by_nivel() (+4 more)

### Community 7 - "test_comparison_charts.py"
Cohesion: 0.07
Nodes (34): metric_label(), metric_legend_suffix(), normalize_group(), _accumulate_running(), _category_color(), generate_chart_current_year(), generate_chart_history(), _last_per_month() (+26 more)

### Community 8 - "report.py"
Cohesion: 0.16
Nodes (23): test_gsc_report_message_lists_sections(), list_indicator_slugs(), _appearance_labels(), build_briefing(), GscBriefing, _hygiene_counts(), _query_stats(), QueryStat (+15 more)

### Community 9 - "scheduler.py"
Cohesion: 0.06
Nodes (45): work_single(), write_calendar_index(), estimated_next_release(), fetch_ibge_calendar(), _match_code(), next_release_for(), _parse_release_date(), refresh_official_dates() (+37 more)

### Community 10 - "package.json"
Cohesion: 0.08
Nodes (30): astro, @astrojs/check, @astrojs/sitemap, @fontsource/fraunces, @fontsource/inter, tailwindcss, @tailwindcss/vite, @types/node (+22 more)

### Community 11 - "is_cron_match"
Cohesion: 0.09
Nodes (8): is_cron_match(), is_due(), next_run(), validate_frequency(), TestIsCronMatch, TestIsDue, TestNextRun, TestValidateFrequency

### Community 12 - "test_wage.py"
Cohesion: 0.19
Nodes (10): _Point, _series(), test_empty_series(), test_highlights_2026_step(), test_steps_collapse_identical_months(), derive_highlights(), derive_steps(), _pct() (+2 more)

### Community 13 - "AGENTS.md"
Cohesion: 0.12
Nodes (12): Hooks (`.claude/settings.json`), MCPs (`.mcp.json`), Python, Skills (`.claude/skills/`), Subagents (`.claude/agents/`), Comandos principais do CLI, Documentação, Features (estado atual — Fases 1, 2 e 4; as Fases 3 e 5 estão só especificadas) (+4 more)

### Community 14 - "notifications.py"
Cohesion: 0.18
Nodes (14): build_success_message(), _credentials(), send_build_error(), send_build_success(), send_collect_error(), send_collect_success(), send_deploy_error(), send_deploy_success() (+6 more)

### Community 15 - "formatters.py"
Cohesion: 0.24
Nodes (12): collect_starting_message(), _fmt_ctr_ratio(), _fmt_delta(), _fmt_int(), _fmt_number(), _fmt_pct(), _fmt_pos(), _fmt_query_line() (+4 more)

### Community 16 - "format.ts"
Cohesion: 0.11
Nodes (21): Props, Props, formatted, Props, IndicatorSummary, IndicatorUnit, IndicatorValue, CATEGORY_LABEL (+13 more)

### Community 17 - "IndicatorTableHistory.astro"
Cohesion: 0.12
Nodes (22): groups, monthIndexByDate, monthlyValues, Props, years, formatAdjustment(), Props, steps (+14 more)

### Community 18 - "BaseLayout.astro"
Cohesion: 0.09
Nodes (11): year, navItems, Props, Props, canonicalUrl, Props, { groups }, meta (+3 more)

### Community 19 - "[category]/index.astro"
Cohesion: 0.11
Nodes (20): colorClass, label, Props, CategoryKey, loadIndex(), categoryLabel(), categorySlug(), CATEGORY_DESCRIPTIONS (+12 more)

### Community 20 - "test_formatters.py"
Cohesion: 0.17
Nodes (20): collect_error_message(), collect_result_message(), collect_summary_message(), _fmt_month(), indicators_message(), _BuildLog, _Indicator, test_collect_error_message_contains_code() (+12 more)

### Community 21 - "data.ts"
Cohesion: 0.11
Nodes (17): CalendarEntry, CalendarIndex, CategorySection, DATA_DIR, Frequency, GroupIndicatorRef, GroupLatest, GroupLatestEntry (+9 more)

### Community 22 - "pages/[slug].astro"
Cohesion: 0.14
Nodes (14): escape(), inline(), renderMarkdown(), detail, index, jsonLd, last12mStr, longHtml (+6 more)

### Community 23 - "handlers.py"
Cohesion: 0.08
Nodes (9): _apply_pending_migrations(), build_application(), main(), _fake_update(), test_authorized_chat_passes(), test_missing_chat_id_blocks(), test_unauthorized_chat_replies_and_skips(), _path_from_env() (+1 more)

### Community 24 - "comparar/[slug].astro"
Cohesion: 0.18
Nodes (8): Props, Group, loadGroups(), getStaticPaths(), { group }, jsonLd, meta, Props

### Community 25 - "build_error_message"
Cohesion: 0.40
Nodes (4): build_error_message(), deploy_error_message(), test_build_error_message(), test_deploy_error_message()

### Community 26 - "DeployResult"
Cohesion: 0.38
Nodes (7): deploy_success_message(), publish_summary_message(), test_deploy_success_message(), test_publish_summary_message_full_success(), test_publish_summary_message_no_changes_in_build(), test_publish_summary_message_no_changes_in_deploy(), DeployResult

### Community 27 - "context7"
Cohesion: 0.33
Nodes (5): npx, uvx, context7, sqlite, @upstash/context7-mcp

### Community 28 - "vercel.json"
Cohesion: 0.33
Nodes (5): buildCommand, framework, installCommand, outputDirectory, redirects

### Community 29 - "tsconfig.json"
Cohesion: 0.40
Nodes (4): astro/tsconfigs/strict, exclude, extends, include

### Community 30 - "Astro Starter Kit: Minimal"
Cohesion: 0.40
Nodes (4): Astro Starter Kit: Minimal, 🧞 Commands, 🚀 Project Structure, 👀 Want to learn more?

### Community 31 - "PeriodFilter.astro"
Cohesion: 0.40
Nodes (3): buttons, Props, VALID

### Community 32 - "allowBuilds"
Cohesion: 0.50
Nodes (3): allowBuilds, esbuild, sharp

### Community 33 - "unauthorized_message"
Cohesion: 0.67
Nodes (3): wrapper(), unauthorized_message(), test_unauthorized_message()

### Community 53 - "BCBSGSConnector"
Cohesion: 0.18
Nodes (12): BCBSGSConnector, _no_pagination_pause(), test_404_returns_empty_list(), test_502_is_retried_then_parsed(), test_connect_error_is_retried_then_parsed(), test_decimal_with_comma_is_parsed(), test_empty_body_is_retried_then_parsed(), test_http_error_raises_fetch_error() (+4 more)

### Community 55 - "IBGESIDRAConnector"
Cohesion: 0.26
Nodes (3): ParseError, RawDataPoint, IBGESIDRAConnector

### Community 57 - "_fmt_iso_local"
Cohesion: 0.22
Nodes (8): errors_message(), _fmt_iso_local(), format_schedule(), logs_message(), status_message(), test_errors_message_empty(), test_logs_message_empty(), test_status_message_without_build()

### Community 58 - "test_notifications.py"
Cohesion: 0.20
Nodes (6): _reset_warning_flag(), test_send_message_noop_when_no_chat_id(), test_send_message_noop_when_no_token(), test_send_message_posts_to_bot_api(), test_send_message_swallows_http_errors(), test_send_message_swallows_network_errors()

## Knowledge Gaps
- **4 isolated node(s):** `npx`, `uvx`, `@upstash/context7-mcp`, `astro/tsconfigs/strict`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 342 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `datetime`, `builder.py`, `test_aggregations.py`, `connection.py`, `test_comparison_charts.py`, `scheduler.py`, `handlers.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **What connects `npx`, `uvx`, `@upstash/context7-mcp` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `datetime` be split into smaller, more focused modules?**
  _Cohesion score 0.063585291113381 - nodes in this community are weakly interconnected._
- **Why does `deploy()` connect `builder.py` to `get_connection`, `connection.py`, `AGENTS.md`, `notifications.py`, `DeployResult`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Should `base.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14245014245014245 - nodes in this community are weakly interconnected._
- **Why does `Hooks (`.claude/settings.json`)` connect `AGENTS.md` to `builder.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05403508771929825 - nodes in this community are weakly interconnected._