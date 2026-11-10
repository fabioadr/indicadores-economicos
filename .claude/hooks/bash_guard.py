#!/usr/bin/env python3
"""PreToolUse guard for the Bash tool.

1. Venv enforcement: python/python3/pip/pytest/ruff must be called as .venv/bin/<tool>.
   Denying with the corrected command saves the model from probing the environment.
2. Deploy confirmation: `git push` and `pipeline.cli deploy|publish` publish the site (Vercel),
   so they always ask, with the reason shown.

Runs with the system python3 on purpose: it must work even when .venv is broken.
"""

from __future__ import annotations

import json
import re
import shlex
import sys

VENV_TOOL_PATTERN = re.compile(r"^(?:/usr(?:/local)?/bin/)?(python3?(?:\.\d+)?|pip3?|pytest|ruff)$")
WRAPPERS = {"time", "nice", "nohup", "exec", "command", "env"}
OPERATORS = {"|", "||", "&&", ";", "&", "|&", "(", ")", ";;", "{", "}", "$("}
DEPLOY_PATTERN = re.compile(r"\bgit\s+push\b|\bpipeline\.cli\s+(deploy|publish)\b")


def _command_starts(command: str) -> list[str]:
    """First word of every simple command, quote-aware (a `|` inside quotes is not a pipe)."""
    starts: list[str] = []
    for line in command.splitlines():
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        try:
            tokens = list(lexer)
        except ValueError:  # unbalanced quotes (e.g. heredoc body line): skip it
            continue
        expecting = True
        for token in tokens:
            if token in OPERATORS:
                expecting = True
                continue
            if not expecting:
                continue
            if ("=" in token and not token.startswith("=")) or token in WRAPPERS:
                continue
            starts.append(token.removeprefix("$"))
            expecting = False
    return starts


def _venv_violation(command: str) -> str | None:
    for first in _command_starts(command):
        if ".venv/bin/" in first:
            continue
        match = VENV_TOOL_PATTERN.match(first)
        if match:
            tool = match.group(1)
            return "python" if tool.startswith("python") else ("pip" if tool.startswith("pip") else tool)
    return None


def _decision(kind: str, reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": kind,
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""

    tool = _venv_violation(command)
    if tool:
        if tool == "pip":
            hint = "uv add <pacote> (dev: uv add --dev <pacote>). O venv não tem pip"
        else:
            hint = f".venv/bin/{tool} <mesmos argumentos>"
        _decision(
            "deny",
            f"Use o venv do projeto: {hint}. O interpretador é fixo (.venv/bin/python, Python 3.14 via uv); "
            "não procure outros nem investigue o ambiente — reexecute com o caminho do venv.",
        )
        return 0

    if DEPLOY_PATTERN.search(command):
        _decision("ask", "Este comando faz git push e dispara deploy em produção na Vercel. Confirme antes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
