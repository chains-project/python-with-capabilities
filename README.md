# python-with-capabilities

This project studies Python runtimes that guardrail AI-agent code with **capabilities**. The goal (see
[`AGENTS.md`](AGENTS.md)) is a runtime with three properties:

- Python syntax and semantics, so that off-the-shelf LLMs use it correctly;
- a declarative capability policy restricting what an agent can do;
- a policy one can reason about and, ideally, prove things about.

The repository holds a survey of prior art and a reproducible benchmark of the existing in-process Python sandboxes
for agent code. Sister project: [bash-with-capabilities](https://github.com/chains-project/bash-with-capabilities).

## Main take-away: Monty is the best

[Monty](https://github.com/pydantic/monty) (Pydantic, Rust) is the best in-process Python sandbox for agents in our
benchmark of 2026-11-21. The others are [Ouros](https://github.com/parcadei/ouros),
[smolagents](https://github.com/huggingface/smolagents)' LocalPythonExecutor,
[RestrictedPython](https://github.com/zopefoundation/RestrictedPython) and [Pyodide](https://pyodide.org).

- 🔐 **No escape, and the richest policy.**
  - Monty blocks all 47 escape probes. Ouros lets `linecache` read a host file. Pyodide in Node runs host commands
    through `os.system` and `pickle`, and opens host sockets.
  - Monty is the only runtime that enforces read-only and read-write path grants (with `MountDir`), an environment
    allowlist, and host-function grants, all with no violation.
  - It has no import allowlist, but it needs none: `os` and `pathlib` are virtual and reach only what is mounted.
- 🧯 **Contains runaway code.** Its time limit cannot be caught by the code it stops: it stops infinite loops,
  exception-swallowing loops, recursion, regex backtracking and huge powers. Memory caps exist
  but are off by default.
- ⚡ **Fast.** Monty runs at 0.95–3.1× CPython's time, with a separate worker process and 26 MiB peak RSS.
  smolagents is 6–100× slower than CPython, and Pyodide needs 3.1 s just to start.

Caveats:

- Monty covers a subset of Python: 75 of 102 conformance scripts match CPython. The gaps are mostly in classes (4/11:
  decorators on methods, `@property`), generators and some stdlib modules. Most failures are loud.
- It has 1 silent error: `round(2.675, 2)` returns `2.68` (fixed upstream in
  [pydantic/monty#1378](https://github.com/pydantic/monty/pull/1378), after 1.6.0).
- Its default pytest-style `assert` messages differ from CPython by design; the benchmark turns them off with
  `assert_message_annotations=False`.
- It cannot run third-party packages.
- Grants other than mounts are host callbacks (code), and its only static check is a type checker, not a policy
  checker.

Pyodide has the best fidelity (100/102, since it is real CPython), but it is not a sandbox in Node. smolagents and
RestrictedPython filter live CPython objects; they block every escape probe here, but have the lowest fidelity: 64
and 51 of 102, with 6 silent errors for smolagents.

## Contents

- [`PRIOR-ART.md`](PRIOR-ART.md): a survey covering:
  - CPython's failed sandboxes (`rexec`, `Bastion`) and object-capability proposals;
  - CaMeL and agent policy layers;
  - in-process runtimes;
  - isolation in containers, microVMs and the kernel.
- [`bench/`](bench/README.md): the benchmark.
  - Five suites, all compared against CPython 3.14:
    - conformance (102 scripts);
    - security escapes (47 probes);
    - strict policies (53 probes, [`bench/POLICY.md`](bench/POLICY.md));
    - resource exhaustion (9 probes);
    - performance (9 tasks).
  - A qualitative rubric with evidence ([`bench/QUALITATIVE.md`](bench/QUALITATIVE.md)).
  - Results: [`bench/results/2026-11-21.md`](bench/results/2026-11-21.md).

## Reproduce

```bash
cd bench
./setup.sh             # one virtualenv per runtime (uv) and Pyodide (npm), pinned versions
./run.py selfcheck     # validate the instruments: CPython is the known positive, a no-op the known negative
./run.py all --json results/$(date +%F).json --report results/$(date +%F).md
```

The harness needs Linux and Python 3 (standard library only). The resource suite also needs `systemd-run --user`,
`prlimit` and GNU `time`.
