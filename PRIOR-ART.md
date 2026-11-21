# Prior art

What exists for this project's goal (see `AGENTS.md`): a Python runtime that guardrails AI-agent code with
capabilities, keeps Python semantics, and makes the capability policy declarative and provable.
This is a snapshot of 2026-11-17, found with web search (WebSearch and `websearch.py`, which covers GitHub, Brave,
Exa and arXiv). The survey is not exhaustive: "nothing combines X and Y" means "nothing found", not "nothing exists".
Sister project: [bash-with-capabilities](https://github.com/chains-project/bash-with-capabilities).

## Summary

Python sandboxing has a long history of failure inside CPython itself. `rexec` and `Bastion` were disabled in Python
2.3, and introspection breaks every attempt to filter a live CPython object graph. The agent era answered in three
ways:

- **Own interpreters with no ambient authority**: Pydantic Monty and Ouros, both in Rust. The host grants functions
  and mounts.
- **Filtered CPython**: smolagents' LocalPythonExecutor and RestrictedPython, which use allowlists, denylists and
  guards over real objects.
- **Real CPython in WebAssembly**: Pyodide.

The research side has CaMeL (Google DeepMind), a custom Python interpreter that attaches capabilities to values and
checks a policy at each tool call.

None of these offers a declarative policy that can be checked statically for full Python. The measured comparison is
in [`bench/`](bench/README.md).

## Research: capabilities and Python

- **`rexec` / `Bastion`** (Python ≤ 2.2): restricted execution modules, disabled in Python 2.3 because of "known
  security holes that were not readily fixable". The new-style classes made introspection escapes worse.
  [Python 2 docs](https://docs.python.org/2.7/_sources/library/restricted.rst.txt),
  [wiki: SandboxedPython](https://wiki.python.org/moin/SandboxedPython).
- **Object capabilities for CPython**: Guido van Rossum proposed object capabilities for securing interpreters, after
  discussions with Mark S. Miller (E). The proposal did not result in a supported mechanism (no outcome found).
  [python-dev thread](https://mail.python.org/archives/list/python-dev@python.org/thread/O2VMSYY2EXV4MTHLZ3CSEJZMDVZCK46L/).
  Later: "Designing secure systems with Object-Capabilities, Python" at
  [PyCon 2016](https://us.pycon.org/2016/schedule/presentation/2248/).
- **PyPy sandbox**: an interpreter build whose system calls go to a controller process. It is historical (see the
  wiki above).
- **CaMeL** (Debenedetti et al., Google DeepMind, 2025; [arXiv:2503.18813](https://arxiv.org/pdf/2503.18813),
  [code](https://github.com/google-research/camel-prompt-injection)):
  - One LLM writes the plan as restricted Python, and a quarantined LLM handles untrusted data.
  - A custom interpreter attaches capabilities (provenance and allowed readers) to every value, and checks Python
    policy functions at every tool call.
  - It claims "no policy violation can occur by construction" on AgentDojo, at some cost in utility.
  - It is the closest research to "Python with provable capabilities", but it covers a restricted subset driven by
    tool calls. Commentary: [Simon Willison](https://simonw.substack.com/p/camel-offers-a-promising-new-direction).
- **Related policy layers for agents**, which act on tool calls rather than Python:
  - Progent ([arXiv:2504.11703](https://arxiv.org/html/2504.11703)): programmable privilege-control policies.
  - AgentBound ([arXiv:2510.21236](https://arxiv.org/pdf/2510.21236)): execution boundaries.
  - CapSeal ([arXiv:2604.16762](https://arxiv.org/pdf/2604.16762)): capability-sealed secrets.

## In-process runtimes for agent code

Compared in [`bench/`](bench/README.md), at the versions pinned in `bench/setup.sh`:

- **Monty** ([pydantic/monty](https://github.com/pydantic/monty), Rust, MIT, `pydantic-monty` 1.6.0, ~8.9k stars):
  - A from-scratch bytecode VM that uses Ruff's parser. It targets a subset of Python 3.14: no generators, and no
    third-party packages (Pydantic says probably never).
  - No ambient authority: filesystem, environment and network do not exist unless granted. Grants are host functions
    (`external_lookup`), `MountDir` mounts (read-only, read-write, or copy-on-write in memory) and an `OSAccess`
    environment.
  - Workers run as separate processes, and resource limits cannot be caught by the sandboxed code.
  - It powers Pydantic AI's "Code Mode" and Logfire Agent Sandboxes. It calls itself production-ready since 1.0.
  - [Announcement](https://pydantic.dev/articles/pydantic-monty),
    [Simon Willison on Monty in WASM](https://simonwillison.net/2026/Feb/6/pydantic-monty/).
- **Ouros** ([parcadei/ouros](https://github.com/parcadei/ouros), Rust, MIT, 0.0.7):
  - A sandboxed runtime related to Monty, with REPL sessions, fork and rewind, and snapshots.
  - Every outside effect (host functions, and also `pathlib` and `os` calls) pauses the VM and hands the host a
    snapshot with the function name and arguments.
  - Its `CapabilitySet` grants match function names only.
  - No commit since April 2026, and no wheel for Python 3.14.
- **smolagents LocalPythonExecutor** ([huggingface/smolagents](https://github.com/huggingface/smolagents), Python,
  Apache-2.0, 1.26.0):
  - An AST-walking interpreter over real CPython objects. Imports go through an allowlist, which always includes a
    base list of modules. It adds dunder-access filters and a "non-exhaustive" denylist of dangerous modules.
  - Its own docs warn that "no local python sandbox can ever be completely secure".
  - Public escape reports exist: [JFrog JFSA-2025-001434277](https://research.jfrog.com/vulnerabilities/smolagents-local-python-sandbox-escape-jfsa-2025-001434277/),
    and CVE-2026-4963 ([write-up](https://baeseokjae.github.io/posts/smolagents-python-executor-code-injection-guide-2026/)).
    Neither is verified against the repository.
- **RestrictedPython** ([zopefoundation/RestrictedPython](https://github.com/zopefoundation/RestrictedPython),
  Python, ZPL, 9.0):
  - Rewrites the AST so that attribute access, item access, iteration, writes and print call guards supplied by the
    host. Its `compile_restricted` rejects some source before running, which is the only check before execution in
    this set, and it is purely syntactic.
  - It is a toolkit: the embedder writes the policy as guard code. Its changelog lists 5 CVEs.
- **Pyodide** ([pyodide](https://pyodide.org), CPython 3.14 compiled to WebAssembly, npm 314.0.8):
  - Gives real CPython semantics and packages.
  - The boundary is the WebAssembly instance plus the JavaScript objects the host exposes. By default `js` is the
    host's `globalThis`, which in Node includes `process`, so it is not a sandbox there.
  - The Deno-based wrappers [pydantic/mcp-run-python](https://github.com/pydantic/mcp-run-python) and
    [langchain-ai/langchain-sandbox](https://github.com/langchain-ai/langchain-sandbox) are both archived as of
    2026.

Not benchmarked:

- [moderately-ai/interpretthis](https://github.com/moderately-ai/interpretthis): a Rust AST interpreter with 0 stars.
- [AnswerDotAI/safepyrun](https://github.com/AnswerDotAI/safepyrun): "safe(ish)".
- [fixed-ai/sandboxed-python](https://github.com/fixed-ai/sandboxed-python): a finite subset, last pushed 2025.
- [RustPython](https://github.com/RustPython/RustPython): a general interpreter, not a sandbox.
- [pyex.dev](https://pyex.dev/): not inspected.

### Benchmark findings (2026-11-21)

Full tables are in `bench/results/2026-11-21.md`, and the evidence per tool is in `bench/QUALITATIVE.md`.

- **Conformance**: the share of 102 scripts that match CPython 3.14 (stdout and exit code):
  - Pyodide: 100;
  - Ouros: 83;
  - Monty: 75;
  - smolagents: 64;
  - RestrictedPython: 51.

  Silent mismatches, which give wrong output with no error:
  - smolagents (6):
    - `@property` returns a bound method;
    - other decorators are ignored;
    - `for … else` never runs its `else`;
    - `print(sep=, end=)` is ignored;
    - `!r` in f-strings is ignored.
  - Ouros (3): `round(2.675, 2)` is wrong, and two `datetime` scripts print an internal source location instead of
    dates.
  - Monty (1): the same `round` error. Its pytest-style `assert` messages are a documented divergence, turned off
    in the benchmark with `assert_message_annotations=False`.

  RestrictedPython compiles the agent's code with its own module's `from __future__ import annotations` inherited, so
  annotations become strings.
- **Security** (47 escape probes, default agent workspace):
  - Monty, smolagents and RestrictedPython block all 47.
  - Ouros leaks one: `linecache.getlines()` reads a host file.
  - Pyodide in Node leaks 12, even with `jsglobals: {}`:
    - `os.system`, `pickle` and `ctypes` run host commands;
    - `socket`, `urllib` and `http.client` open host connections;
    - `js.constructor.constructor` and `pyodide_js.constructor.constructor` reach `process`.
- **Strict policies** (4 scenarios, 53 probes):
  - Host-function grants: all five enforce them, and no reflective path reaches the host: `__globals__`, a computed
    `getattr`, a descriptor, a format string, the function's module, or rebuilding a function from its code object.
  - Path grants: only Monty can express them, and it enforces them exactly. Pyodide's NODEFS has no read-only mode;
    the others have no file access at all.
  - Environment allowlist: Monty, Ouros and Pyodide enforce it. smolagents and RestrictedPython cannot express it,
    because an allowed `os` module sees the host environment.
  - Import allowlist: only smolagents and RestrictedPython can express one. smolagents blocks all 12 bypasses.
    RestrictedPython lets `json.codecs.open()` read a file, because `json` re-exports `codecs`.
  - RestrictedPython's compile-time check rejects 12 of 21 deny probes before running; the rest pass to its runtime
    guards.
- **Resource limits**:
  - Monty contains 6 of 9 probes with its own limits. The memory probes need `max_memory`, which is off by default,
    and its output flood hit the harness cap.
  - Ouros contains 4 and refuses `time.sleep`.
  - smolagents contains only the infinite loop: its timeout cannot kill a thread stuck in C, such as a regex, a big
    power or a sleep.
  - RestrictedPython contains only recursion.
  - Pyodide contains none.
- **Performance** (median of 5 runs): CPython 57 ms startup, Monty 111 ms, Ouros 42 ms, smolagents 491 ms, Pyodide
  3.1 s.
  - Monty runs computation at 0.95–3.1× CPython's time, and Ouros at 1.0–6.0×.
  - smolagents' AST walker is 6–100× slower than CPython (recursive fib(25): 6.7 s, against 0.07 s).
  - RestrictedPython's `limited_builtins` caps `range()` at 1000 elements, so most perf tasks fail.

## Isolation outside the interpreter

These run full CPython; their policy acts on the process, container or VM, not on Python semantics.

- **Containers and microVMs**: [E2B](https://github.com/e2b-dev/code-interpreter),
  [llm-sandbox](https://github.com/vndee/llm-sandbox) (Docker, Kubernetes, Podman), Daytona,
  [Blaxel](https://blaxel.ai/blog/python-sandbox-llm-untrusted-code-isolation).
- **Kernel-level**: [nono.sh](https://nono.sh/python-sandbox) (Landlock and Seatbelt), and
  [openedx/codejail](https://github.com/openedx/codejail) (AppArmor).
- **Lesson from the field**: the AWS Bedrock AgentCore Code Interpreter "network isolation mode" leaked over DNS, and
  its metadata service exposed credentials (Unit 42, April 2026; summarized in
  [OWASP AISVS C09-03](https://github.com/OWASP/AISVS/blob/main/1.0/research/chapters/C09-Orchestration-and-Agents/C09-03-Tool-and-Plugin-Isolation.md)).
  A sound sandbox inside an unsound perimeter still leaks.
