"""smolagents LocalPythonExecutor: grants map to authorized imports and additional functions."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import granted_functions, parse_args, unsupported
from smolagents.local_python_executor import BASE_BUILTIN_MODULES, LocalPythonExecutor

strict, policy, work, code = parse_args()
imports = policy.get("imports", [])
if "imports" in policy and not set(BASE_BUILTIN_MODULES) <= set(imports):
    unsupported(strict, f"base modules are always authorized: {sorted(set(BASE_BUILTIN_MODULES) - set(imports))}")
if policy.get("fs"):
    unsupported(strict, "no filesystem grant (files only through additional functions the embedder writes)")
if "env" in policy:
    unsupported(strict, "no environment virtualization (an authorized os module sees the host environment)")
os.chdir(work)
ex = LocalPythonExecutor(additional_authorized_imports=imports, max_print_outputs_length=10**7,
                         additional_functions=granted_functions(policy), timeout_seconds=10)
ex.send_tools({})
try:
    out = ex(code)
    sys.stdout.write(out.logs)
except Exception as e:  # noqa: BLE001 - every interpreter error is the script's failure
    sys.stdout.write(str(ex.state.get("_print_outputs", "")))
    print(f"{type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
