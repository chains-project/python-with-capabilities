"""Pydantic Monty: grants map to external functions, MountDir mounts and an OSAccess environment."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pydantic_monty as pm
from common import granted_functions, parse_args, unsupported

strict, policy, work, code = parse_args()
if "imports" in policy:
    unsupported(strict, "no import allowlist: the set of built-in modules is fixed")
mounts = [pm.MountDir(host_path=str(work / rel), virtual_path=os.path.normpath(f"/work/{rel}"),
                      mode={"ro": "read-only", "rw": "read-write"}[mode])
          for rel, mode in policy.get("fs", {}).items()]
os_cb = pm.OSAccess(environ=policy["env"]) if "env" in policy else None


def emit(stream: str, text: str) -> None:
    (sys.stdout if stream == "stdout" else sys.stderr).write(text)
    sys.stdout.flush()


# assert_message_annotations=False: Monty's default pytest-style assert messages are a documented, opt-out
# divergence (docs/limitations/assert.md); we score its CPython-compatible mode.
try:
    with pm.Monty() as pool, pool.checkout(limits={"max_feed_duration_secs": 10.0},
                                          assert_message_annotations=False) as session:
        session.feed_run(code, external_lookup=granted_functions(policy), print_callback=emit,
                         mount=mounts or None, cwd="/work" if mounts else None, os=os_cb)
except pm.MontyError as e:
    print(f"{type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
