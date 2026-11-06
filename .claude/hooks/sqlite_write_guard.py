#!/usr/bin/env python3
"""PreToolUse guard for mcp__sqlite__write_query.

Project rule: data and schema change through versioned migrations, never by hand.
Any write via MCP asks for confirmation; destructive statements get an explicit warning.
"""

from __future__ import annotations

import json
import re
import sys

DESTRUCTIVE = re.compile(
    r"\bDROP\s+(TABLE|INDEX|VIEW)\b|\bTRUNCATE\b|\bALTER\s+TABLE\b|\bDELETE\s+FROM\s+\w+\s*(;|$)|\bUPDATE\s+\w+\s+SET\b(?![\s\S]*\bWHERE\b)",
    re.IGNORECASE,
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    query = (payload.get("tool_input") or {}).get("query") or ""
    reason = "Escrita direta no SQLite: a regra do projeto é alterar dados/schema via migration em pipeline/db/migrations/."
    if DESTRUCTIVE.search(query):
        reason = "SQL DESTRUTIVO (DROP/TRUNCATE/ALTER ou DELETE/UPDATE sem WHERE). " + reason
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
