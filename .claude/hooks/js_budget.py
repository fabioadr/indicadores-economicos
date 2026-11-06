#!/usr/bin/env python3
"""PostToolUse (Bash): after a site build, check the client JS budget (~5KB gzipped total).

Policy from docs/PROJECT-CONTEXT.md: minimal JS, no framework. Warns, never blocks.
"""

from __future__ import annotations

import gzip
import json
import os
import re
import sys
from pathlib import Path

BUDGET_BYTES = 5 * 1024
BUILD_PATTERN = re.compile(r"\bpnpm\s+(run\s+)?build\b|\bastro\s+build\b")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not BUILD_PATTERN.search(command):
        return 0

    dist = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / "site" / "dist"
    if not dist.is_dir():
        return 0
    total = sum(len(gzip.compress(p.read_bytes())) for p in dist.rglob("*.js"))
    if total > BUDGET_BYTES:
        message = f"JS do site: {total} bytes gzipped, acima do orçamento de {BUDGET_BYTES} bytes (política: JS mínimo, sem framework)."
        print(json.dumps({
            "systemMessage": message,
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message},
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
