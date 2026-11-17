"""RestrictedPython: compile_restricted plus the documented guards; grants map to an import allowlist and globals.

RestrictedPython is a toolkit: the embedder supplies the guards. This adapter uses the library's own defaults
(safe/limited/utility builtins, safer_getattr, guarded iteration and unpacking, full_write_guard) and the
allowlisting import hook from docs/usage/security_considerations.rst.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import granted_functions, parse_args, unsupported
from RestrictedPython import (
    compile_restricted,
    limited_builtins,
    safe_builtins,
    utility_builtins,
)
from RestrictedPython.Eval import default_guarded_getitem, default_guarded_getiter
from RestrictedPython.Guards import (
    full_write_guard,
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
    safer_getattr,
)

check = "--check" in sys.argv
if check:
    sys.argv.remove("--check")
strict, policy, work, code = parse_args()
if check:
    # The only pre-execution verdict RestrictedPython gives: compile_restricted rejects the source ("denied"),
    # or accepts it and leaves the decision to the runtime guards ("indeterminate").
    import json
    try:
        compile_restricted(code, "main.py", "exec")
        print(json.dumps({"status": "indeterminate"}))
    except SyntaxError as e:
        print(json.dumps({"status": "denied", "reason": str(e)}))
    sys.exit(0)
if policy.get("fs"):
    unsupported(strict, "no filesystem grant (open is not among the safe builtins)")
if "env" in policy:
    unsupported(strict, "no environment virtualization (an allowed os module sees the host environment)")
allowed = frozenset(policy.get("imports", []))


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level != 0:
        raise ImportError("relative imports are not allowed")
    if name.split(".")[0] not in allowed:
        raise ImportError(f"{name!r} may not be imported")
    return __import__(name, globals, locals, fromlist, level)


class StdoutPrint:
    """`print` target: write through to stdout (RestrictedPython's PrintCollector buffers into `printed`)."""

    def __init__(self, _getattr_=None):
        pass

    def _call_print(self, *objects, **kwargs):
        kwargs.pop("file", None)
        print(*objects, **kwargs)

    def __call__(self):
        return ""


def inplacevar(op, x, y):
    import operator
    ops = {"+=": operator.iadd, "-=": operator.isub, "*=": operator.imul, "/=": operator.itruediv,
           "//=": operator.ifloordiv, "%=": operator.imod, "**=": operator.ipow, "<<=": operator.ilshift,
           ">>=": operator.irshift, "&=": operator.iand, "|=": operator.ior, "^=": operator.ixor,
           "@=": operator.imatmul}
    return ops[op](x, y)


builtins = {**safe_builtins, **limited_builtins, **utility_builtins, "__import__": guarded_import}
glb = {"__builtins__": builtins, "__name__": "__main__", "__metaclass__": type, "_getattr_": safer_getattr,
       "_getitem_": default_guarded_getitem, "_getiter_": default_guarded_getiter,
       "_iter_unpack_sequence_": guarded_iter_unpack_sequence, "_unpack_sequence_": guarded_unpack_sequence,
       "_write_": full_write_guard, "_print_": StdoutPrint, "_inplacevar_": inplacevar,
       "_apply_": lambda f, *a, **k: f(*a, **k), **granted_functions(policy)}
os.chdir(work)
try:
    byte_code = compile_restricted(code, "main.py", "exec")
    exec(byte_code, glb)  # noqa: S102 - restricted bytecode, the point of the adapter
except Exception as e:  # noqa: BLE001 - compile-time rejections and runtime errors alike
    sys.stdout.flush()
    print(f"{type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
