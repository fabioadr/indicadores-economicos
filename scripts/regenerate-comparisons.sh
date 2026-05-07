#!/usr/bin/env bash
# Regenera apenas os PNGs comparativos e o groups.json, sem rodar o build completo.
# Útil quando se altera apenas pipeline/config_groups.py.
set -e

.venv/bin/python - <<'PY'
from datetime import datetime, timezone
from pathlib import Path

from pipeline import config
from pipeline.config_groups import INDICATOR_GROUPS
from pipeline.core import builder, comparison_charts
from pipeline.db.connection import get_connection

charts_dir = config.SITE_CHARTS_DIR
data_dir = config.SITE_DATA_DIR
charts_dir.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(parents=True, exist_ok=True)

generated_at = datetime.now(tz=timezone.utc).isoformat()

conn = get_connection(config.DB_PATH)
try:
    for group in INDICATOR_GROUPS:
        png_path = charts_dir / f"compare-{group['slug']}.png"
        ok = comparison_charts.generate_comparison_chart(conn, group, png_path)
        flag = "✓" if ok else "(empty)"
        print(f"{flag} {png_path}")

    groups_path = builder.write_groups_index(
        conn, INDICATOR_GROUPS, data_dir, generated_at,
        charts_url_prefix="/charts",
    )
    print(f"✓ {groups_path}")
finally:
    conn.close()
PY
