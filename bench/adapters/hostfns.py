"""Host functions a policy can grant to sandboxed code (the `functions` key of a policy, see POLICY.md).

The module imports os and subprocess on purpose: real tool modules do, so a sandbox that lets code reach a granted
function's `__globals__` hands out the whole host.
"""
from __future__ import annotations

import os  # noqa: F401 - escape target, see the docstring
import subprocess  # noqa: F401 - escape target, see the docstring

FRUIT = {"apple": 3, "banana": 5}


def lookup(key: str) -> str:
    """The benign tool: a dictionary lookup."""
    return str(FRUIT.get(key, 0))


def admin_reset() -> str:
    """A privileged tool that is never granted; the marker shows it ran on the host."""
    print("ADMIN" + "RAN", flush=True)
    return "done"


CATALOG = {"lookup": lookup, "admin_reset": admin_reset}
