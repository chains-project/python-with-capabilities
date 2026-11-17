# Benchmark: Python runtimes for sandboxing AI-agent code

This benchmark compares Monty, Ouros, smolagents' LocalPythonExecutor, RestrictedPython and Pyodide with CPython 3.14.
Background on each tool is in [`../PRIOR-ART.md`](../PRIOR-ART.md).

## Usage

```bash
./setup.sh                    # one virtualenv per runtime and Pyodide, into .tools/ (uv, node, npm, git)
./run.py selfcheck            # validate the instruments first (see below)
./run.py all --json results/$(date +%F).json --report results/$(date +%F).md
./run.py policy --tools monty --only fs          # a subset
```

`run.py` needs only the Python 3 standard library. The resource suite also needs `systemd-run --user`, `prlimit` and
GNU `time`.

Every tool runs through an adapter in `adapters/`, which reads a policy ([`POLICY.md`](POLICY.md)), a working
directory and a script. Outside the policy suite, all tools run the permissive agent workspace `DEFAULT_POLICY`:
common pure standard-library modules plus the host function `lookup`. Cases are `#### name` blocks in
`cases/<suite>/*.py`; the file name is the case group.

## Quantitative suites

- **conformance**: 102 scripts in 9 groups (basics, strings, collections, functions, classes, control, exceptions,
  stdlib, agent). stdout and exit code are compared with CPython 3.14. A mismatch is classified as:
  - **loud**: the runtime signalled a problem, either with stderr output or a different non-zero exit code;
  - **silent**: wrong output and no signal. These are the worst for an agent, which will trust the result.
- **security**: 47 escape probes in five kinds, each detected on the host. They are run under the default
  workspace, where `lookup` is granted:
  - read: a secret token outside the workdir shows up in the output;
  - write and exec: the host directory outside the workdir changed;
  - net: a TCP listener on the harness side received a connection;
  - env: a host environment token leaked.

  The probes cover the classic Python breakouts:
  - `__subclasses__` walks;
  - `__globals__` of a granted function, also reached through `getattr` with a computed name, a descriptor or a
    format string;
  - generator and traceback frames;
  - `sys.modules`, and private module attributes (`random._os`);
  - `pickle`, `ctypes`;
  - Pyodide's `js` and `pyodide_js`.
- **policy**: 4 scenarios with 53 probes, each tool under its strictest configuration:
  - an import allowlist;
  - host-function grants (with reflective paths to the host);
  - path grants (`src` read-only, `out` read-write);
  - an environment allowlist.

  Probes either must work (`allow`) or must have no effect on the host (`deny`). The report gives one of three
  results per tool and scenario:
  - ✅ enforced exactly;
  - ❌ a deny probe had an effect;
  - `n/a (reason)` when the tool cannot express the policy.

  It also gives RestrictedPython's compile-time verdicts.
- **resource**: 9 exhaustion probes:
  - an infinite loop;
  - recursion that keeps catching its own `RecursionError`;
  - string and list memory growth;
  - a huge power;
  - an output flood;
  - regex backtracking;
  - sleep;
  - a loop that swallows every exception.

  A probe counts as *contained* only if the runtime ends the run itself: before the harness's 20 s deadline, without
  being killed by a signal, under 1.5 GiB RSS, and under 90% of the 200 MB output and disk caps. Runs happen inside a
  systemd scope (MemoryMax 2G, TasksMax 256) with `prlimit --fsize`.
- **perf**: 9 tasks: startup, a loop of 1M iterations, recursive fib(25), string building, dict operations, sorting,
  a JSON round trip, a regex over 1 MB, and method calls. The metrics are median wall time (`-n` repeats) and peak
  RSS. Outputs are also checked against CPython, so a fast but wrong runtime is flagged.

## Qualitative rubric

[`QUALITATIVE.md`](QUALITATIVE.md) answers 12 criteria per tool, each with a file and line or a URL as evidence:

- embedding;
- execution model;
- language coverage;
- packages;
- capability model;
- filesystem, network, environment and subprocess;
- static checking;
- limits;
- known escapes;
- testing;
- maturity;
- relevance.

## Instrument validation

`run.py selfcheck` must print only ✅. It uses two controls: `cpython`, which ignores every policy and gets every
host function (the known positive), and `null`, which runs nothing (the known negative). It checks:

- **conformance**: CPython against CPython gives 102/102;
- **security**: every escape works under CPython, except the Pyodide-only and `ctypes` probes, which need that
  runtime; none works under `null`;
- **policy**: every effect is observed under CPython and none under `null`;
- **resource**: CPython is not contained on any probe, and `null` is contained on all.

## Configuration and caveats

- **Monty**: `limits={'max_feed_duration_secs': 10}` only. `max_memory` exists but is off by default, so the memory
  probes are reported as not contained.
- **Ouros**: `limits={'max_duration_secs': 10}`. Its wheel has no CPython 3.14 build, so it runs in a 3.13 virtualenv.
- **smolagents**: `timeout_seconds=10`; its base modules are always authorized.
- **RestrictedPython**: a toolkit, so the adapter supplies the library's default guards (safe, limited and utility
  builtins, `safer_getattr`, guarded iteration and unpacking, `full_write_guard`) and the allowlisting import hook
  from its documentation. `print` writes straight to stdout.
- **Pyodide**: Node, with `jsglobals: {}` (the documented way to narrow the JavaScript side) and a 10 s timer.
  Packages are not loaded.
- The environment is `LC_ALL=C.UTF-8`, `TZ=UTC`, `PYTHONHASHSEED=0`. Conformance compares stdout and exit code only.
