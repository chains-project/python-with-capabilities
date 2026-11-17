"""Shared adapter plumbing: argument parsing, policy loading, exit codes (see POLICY.md)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

UNSUPPORTED = 99


def parse_args() -> tuple[bool, dict, Path, str]:
    """[--strict] POLICY.json WORKDIR SCRIPT.py -> (strict, policy, workdir, code)."""
    args = sys.argv[1:]
    strict = bool(args) and args[0] == "--strict"
    if strict:
        args = args[1:]
    if len(args) != 3:
        sys.exit(f"usage: {sys.argv[0]} [--strict] POLICY.json WORKDIR SCRIPT.py")
    return strict, json.loads(Path(args[0]).read_text()), Path(args[1]), Path(args[2]).read_text()


def unsupported(strict: bool, why: str) -> None:
    """In strict mode a policy key the tool cannot express ends the run with exit 99."""
    if strict:
        print(f"unsupported: {why}", file=sys.stderr)
        sys.exit(UNSUPPORTED)


def granted_functions(policy: dict) -> dict:
    from hostfns import CATALOG

    return {name: CATALOG[name] for name in policy.get("functions", [])}
