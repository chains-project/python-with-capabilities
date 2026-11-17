# Benchmark policy format

The `policy` suite states each scenario once, in one tool-neutral format. A per-tool adapter (`adapters/`)
translates that policy into the tool's own configuration. With `--strict` (used by the policy suite), an adapter
that cannot express a key exits with code 99 and prints a reason starting with `unsupported:`; the report shows
these as `n/a (reason)`. Without `--strict` (all other suites), adapters apply what they can and ignore the rest.

## Format

A JSON object. Every key is optional; a missing key leaves that dimension at the tool's default.

```json
{
  "imports": ["json", "math"],
  "functions": ["lookup"],
  "fs": {"src": "ro", "out": "rw"},
  "env": {"VISIBLE": "visible-value"}
}
```

- `imports`: the modules that may be imported. Any other module is denied, however it is reached:
  - `__import__` or `importlib`;
  - `exec`;
  - `sys.modules`;
  - a private attribute of an allowed module, such as `random._os` or `json.codecs`;
  - `object.__subclasses__()`.
- `functions`: the host functions the code may call, from the catalog in `adapters/hostfns.py`:
  - `lookup`: benign, the one granted;
  - `admin_reset`: privileged, never granted.

  The catalog module imports `os` and `subprocess`, so any reflective path from a granted function to its globals
  (`__globals__`, `getattr` with a computed name, a descriptor, a format string, the function's module) is a way to
  reach the host.
- `fs`: paths relative to the working directory, each mapped to `ro` or `rw`. Anything not granted can be neither
  read nor written, including through `..`, globs, symlinks, or an absolute host path. The working directory is the
  host directory given to the adapter, and effects are checked there.
- `env`: the complete environment the code sees. Host variables (the harness sets `HIDDEN_TOKEN`) must not leak.

Outside the policy suite, every tool runs under the permissive agent workspace `DEFAULT_POLICY` from `run.py`: common
pure standard-library modules plus `lookup`.

## Probes

`cases/policy/<scenario>.py` holds a `# policy:` header line with the JSON above, followed by probes:

```
#### allow:NAME CHECK      the effect must happen; if it does not, the probe is over-denied
#### deny:NAME CHECK       the effect must not happen; if it does, the probe is VIOLATED
```

`CHECK` is observed on the host, never taken from the tool's own report:

- `stdout~TEXT`: TEXT appears in stdout or stderr. Markers are built so the script text cannot contain them: the
  script prints `'OSRAN' + str(len(os.sep))`, so `OSRAN1` appears only if `os` code actually ran.
- `host+PATH`: PATH was created.
- `host-PATH`: PATH was removed.
- `hostchg PATH`: PATH's content changed.

The harness substitutes these placeholders:

- `@TOKEN@`: a per-run secret, written to `secrets/key.txt`;
- `@ENVTOKEN@`: a per-run secret in the host environment, as `HIDDEN_TOKEN`;
- `@WORK@`: the absolute path of the host working directory;
- `@SECRET@`: a secret file outside the working directory.

## Static check

When a tool can judge a script before running it, the harness also asks it for a verdict, recorded per probe as
denied or indeterminate. RestrictedPython's `compile_restricted` is the only such check in this set: rejected source
counts as "denied", and accepted source as "indeterminate", because its runtime guards still decide.

## Controls

`run.py selfcheck` validates every suite with two controls:

- `cpython`, which ignores the policy and gets every host function (the known positive): every effect must be
  observed;
- `null`, which runs nothing (the known negative): no effect may be observed.
