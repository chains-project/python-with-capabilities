"""Plain CPython: ignores the policy (the oracle and the known-positive control), only supplies what it grants."""
from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import parse_args
from hostfns import CATALOG

strict, policy, work, code = parse_args()
os.chdir(work)
os.environ.update(policy.get("env", {}))
glb = {"__name__": "__main__", **CATALOG}  # every host function, granted or not
sys.path.pop(0)  # the adapter directory must not shadow the script's imports
try:
    exec(compile(code, "main.py", "exec", dont_inherit=True), glb)  # noqa: S102 - the oracle runs the script as is
except SystemExit:
    raise
except BaseException:  # noqa: BLE001 - report every failure of the script
    traceback.print_exc()
    sys.exit(1)
