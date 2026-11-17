"""Ouros: grants map to external functions and an OSAccess environment; there are no host mounts."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ouros
from common import granted_functions, parse_args, unsupported

strict, policy, work, code = parse_args()
if "imports" in policy:
    unsupported(strict, "no import allowlist: the set of built-in modules is fixed")
if policy.get("fs"):
    unsupported(strict, "no host directory mounts (files only through an embedder-written os callback)")
fns = granted_functions(policy)
os_cb = ouros.OSAccess(environ=policy["env"]) if "env" in policy else None


def emit(stream: str, text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


try:
    box = ouros.Sandbox(code, external_functions=list(fns))
    box.run(external_functions=fns, print_callback=emit, os=os_cb, limits={"max_duration_secs": 10.0})
except ouros.SandboxError as e:
    print(f"{type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
