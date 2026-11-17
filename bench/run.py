#!/usr/bin/env python3
"""Benchmark in-process Python sandboxes for AI-agent code against CPython.

Suites:
  conformance  same script: stdout and exit code compared with CPython 3.14 (the oracle). Mismatches are split
               into "loud" (the runtime signalled a problem: stderr or a different non-zero exit) and "silent"
               (wrong output, no signal) -- silent ones mislead agents.
  security     escape probes (read/write/exec/net/env beyond what is granted), detected on the host.
  policy       each tool under its strictest configuration for one tool-neutral policy (POLICY.md).
  resource     exhaustion probes run in a systemd scope; "contained" = the runtime stopped itself.
  perf         wall time (median of N) and peak RSS on common tasks; output also checked against CPython.

Instrument controls: `cpython` (ignores every policy) must score 100% conformance and show every escape and
policy effect (known positive); `null` (runs nothing) must show none (known negative). `run.py selfcheck`.

Usage: run.py [conformance|security|policy|resource|perf|all|selfcheck] [--tools a,b] [--only SUBSTR]
              [--json OUT] [--report OUT.md] [--from-json IN] [-n REPEATS] [-j JOBS]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import platform
import re
import secrets
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS_DIR = HERE / ".tools"
ADAPTERS = HERE / "adapters"
CASES = HERE / "cases"
FIXTURE = HERE / "fixture"
TIMEOUT = 20.0  # harness deadline per run (s); runtimes are configured with 10 s where they support it
OUT_CAP = 50 * 1024 * 1024
FSIZE_CAP = 200 * 1024 * 1024
MEM_CAP = "2G"

ALL_TOOLS = ["cpython", "monty", "ouros", "smolagents", "restrictedpython", "pyodide"]

# The capabilities of the permissive "agent workspace" used outside the policy suite: common pure stdlib modules
# (a superset of smolagents' always-authorized base modules) and the benign host function `lookup`.
STD_IMPORTS = ["bisect", "collections", "copy", "dataclasses", "datetime", "decimal", "enum", "fractions",
               "functools", "heapq", "itertools", "json", "math", "operator", "queue", "random", "re", "stat",
               "statistics", "string", "textwrap", "time", "typing", "unicodedata"]
DEFAULT_POLICY = {"imports": STD_IMPORTS, "functions": ["lookup"]}

BASE_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LC_ALL": "C.UTF-8", "TZ": "UTC", "HOME": "/nonexistent",
            "PYTHONHASHSEED": "0"}


def adapter_argv(tool: str, policy_file: Path, work: Path, script_file: Path, strict: bool = False,
                 check: bool = False) -> list[str] | None:
    """Command line running script_file under the policy; None for `check` when the tool has no static check."""
    flag = ["--strict"] if strict else []
    rest = [str(policy_file), str(work), str(script_file)]
    if check:
        return ([str(TOOLS_DIR / "venv-restrictedpython/bin/python"), str(ADAPTERS / "restrictedpython_adapter.py"),
                 "--check", *rest] if tool == "restrictedpython" else None)
    if tool == "null":
        return ["true"]
    if tool == "pyodide":
        return ["node", str(ADAPTERS / "pyodide_adapter.mjs"), *flag, *rest]
    venv = {"cpython": "oracle"}.get(tool, tool)
    return [str(TOOLS_DIR / f"venv-{venv}/bin/python"), "-I", str(ADAPTERS / f"{tool}_adapter.py"), *flag, *rest]


def make_env(extra: dict | None = None) -> dict:
    return {**BASE_ENV, "HIDDEN_TOKEN": "not-a-secret", **(extra or {})}


def new_workspace() -> tuple[Path, Path, Path, str]:
    """root/{work,outside/secret.txt}; the script and policy files go in root, outside the grant."""
    root = Path(tempfile.mkdtemp(prefix="pybench-"))
    work, outside = root / "work", root / "outside"
    shutil.copytree(FIXTURE, work)
    for p in [work, *work.rglob("*")]:  # normalise: the user's umask must not change results
        p.chmod(0o755 if p.is_dir() else 0o644)
    outside.mkdir()
    token = "TOKEN-" + secrets.token_hex(8)
    (outside / "secret.txt").write_text(token + "\n")
    return root, work, outside, token


def run_in(tool: str, root: Path, work: Path, script: str, policy: dict, env: dict, strict: bool = False,
           sandboxed: bool = False) -> Run:
    (root / "main.py").write_text(script)
    (root / "policy.json").write_text(json.dumps(policy))
    return execute(adapter_argv(tool, root / "policy.json", work, root / "main.py", strict), work, env, sandboxed)


def snapshot(d: Path) -> dict[str, tuple[int, int, int]]:
    """Listing of root and outside/ (not work/, not the harness's own files), to detect writes beyond the grant."""
    res = {}
    for p in [d, *d.glob("*"), *(d / "outside").rglob("*")]:
        if p == d / "work" or p.name in ("main.py", "policy.json"):
            continue
        st = p.lstat()
        res[str(p.relative_to(d))] = (st.st_size, st.st_mtime_ns, st.st_ino)
    res.pop(".", None)  # root's own mtime changes when the harness writes main.py
    return res


@dataclass
class Case:
    suite: str
    group: str
    name: str
    script: str

    @property
    def id(self) -> str:
        return f"{self.group}/{self.name}"


def load_cases(suite: str) -> list[Case]:
    out: list[Case] = []
    for f in sorted((CASES / suite).glob("*.py")):
        name, buf = None, []
        for line in f.read_text().splitlines(keepends=True) + ["#### \n"]:
            if line.startswith("#### "):
                if name:
                    out.append(Case(suite, f.stem, name, "".join(buf).rstrip("\n") + "\n"))
                name, buf = line[5:].strip(), []
            elif name is not None:
                buf.append(line)
    return out


@dataclass
class Run:
    stdout: bytes
    stderr: bytes
    exit: int | None  # None = killed by the harness deadline
    wall: float
    maxrss_kb: int
    signal: int | None = None
    extra: dict = field(default_factory=dict)


def execute(argv: list[str], cwd: Path, env: dict, sandboxed: bool = False, timeout: float = TIMEOUT) -> Run:
    """Run argv with stdout/stderr to files, a deadline, and peak RSS measured by GNU time.

    Peak RSS comes from /usr/bin/time, not from wait4: a child forked from this Python process
    reports Python's own RSS as its floor. When sandboxed, the command runs in a systemd user scope
    (memory, task limits) under prlimit (file size limit); `env -i` then restores the clean env.
    """
    with tempfile.TemporaryFile() as fo, tempfile.TemporaryFile() as fe, tempfile.NamedTemporaryFile("r") as ft:
        argv = ["/usr/bin/time", "-f", "%M", "-o", ft.name] + argv
        run_env = env
        if sandboxed:
            argv = (["systemd-run", "--user", "--scope", "-q", "-p", f"MemoryMax={MEM_CAP}", "-p", "MemorySwapMax=0",
                     "-p", "TasksMax=256", "prlimit", f"--fsize={FSIZE_CAP}", "--", "env", "-i"]
                    + [f"{k}={v}" for k, v in env.items()] + argv)
            run_env = {**env, **{k: os.environ[k] for k in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS")
                                 if k in os.environ}}
        t0 = time.monotonic()
        p = subprocess.Popen(argv, cwd=cwd, env=run_env, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe,
                             start_new_session=True)
        killed = False
        while True:
            pid, status, _ = os.wait4(p.pid, os.WNOHANG)
            if pid:
                break
            if time.monotonic() - t0 > timeout:
                killed = True
                try:
                    os.killpg(p.pid, 9)
                except ProcessLookupError:
                    pass
                _, status, _ = os.wait4(p.pid, 0)
                break
            time.sleep(0.002)
        wall = time.monotonic() - t0
        p.returncode = 0  # reaped by wait4; keep Popen from complaining
        if not killed:  # kill leftovers (backgrounded children) of the session
            try:
                os.killpg(p.pid, 9)
            except (ProcessLookupError, PermissionError):
                pass
        out_size = os.fstat(fo.fileno()).st_size + os.fstat(fe.fileno()).st_size
        fo.seek(0)
        fe.seek(0)
        out, err = fo.read(OUT_CAP + 1), fe.read(OUT_CAP + 1)
        tail = ft.read().strip().splitlines()
    if sandboxed and b"Failed to" in err[:300] and b"bus" in err[:300]:
        raise SystemExit(f"systemd-run could not create a scope: {err[:300]!r}")
    # GNU time prefixes "Command terminated by signal N" / "Command exited with non-zero status N".
    rss = int(tail[-1]) if tail and tail[-1].isdigit() else -1
    sig = next((int(l.rsplit(" ", 1)[1]) for l in tail if l.startswith("Command terminated by signal")), None)
    if os.WIFSIGNALED(status):
        sig = os.WTERMSIG(status)
    code = None if killed else (128 + sig if sig else os.WEXITSTATUS(status))
    return Run(out, err, code, wall, rss, sig, {"out_size": out_size})


def classify(ref: Run, got: Run) -> str:
    if got.exit is None:
        return "timeout"
    if got.stdout == ref.stdout and got.exit == ref.exit:
        return "pass"
    signalled = (got.exit != ref.exit and got.exit != 0) or (got.stderr.strip() and not ref.stderr.strip())
    return "loud" if signalled else "silent"


class Listener:
    def __init__(self) -> None:
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(16)
        self.sock.settimeout(0.2)
        self.port = self.sock.getsockname()[1]
        self.hits = 0
        self._stop = False
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self) -> None:
        while not self._stop:
            try:
                c, _ = self.sock.accept()
                self.hits += 1
                c.close()
            except OSError:
                pass

    def close(self) -> None:
        self._stop = True
        self.sock.close()


class HttpListener:
    """Records (path, Host header) of every HTTP request; /allowed/redirect answers 302 to /denied-redirect."""

    def __init__(self) -> None:
        import http.server

        hits = self.hits = []

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                hits.append((self.path, self.headers.get("Host", "")))
                if self.path == "/allowed/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/denied-redirect")
                else:
                    self.send_response(200)
                self.send_header("Content-Length", "3")
                self.end_headers()
                self.wfile.write(b"ok\n")

            do_POST = do_GET

            def log_message(self, *a: object) -> None:
                pass

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.srv.shutdown()
        self.srv.server_close()


def effect_happened(check: str, run: Run, work: Path, before: dict[str, bytes], hits: list) -> bool:
    if check.startswith("stdout~"):
        return check[7:].encode() in run.stdout + run.stderr
    if check.startswith("host+"):
        q = work / check[5:]
        return q.exists() or q.is_symlink()
    if check.startswith("host-"):
        return not (work / check[5:]).exists()
    if check.startswith("hostchg "):
        q = work / check[8:]
        return not q.exists() or q.read_bytes() != before[check[8:]]
    if check.startswith("net~"):
        want, _, host = check[4:].partition("@")
        return any(path == want and (not host or h.split(":")[0] == host) for path, h in hits)
    raise SystemExit(f"bad check {check!r}")


def dir_bytes(d: Path) -> int:
    return sum(p.lstat().st_size for p in d.rglob("*"))


REFUSAL = re.compile(r"not supported|unsupported|parse error|command not found|command not allowed|"
                     r"not allowed|permission denied", re.IGNORECASE)


def resource_verdict(row: dict) -> dict:
    """contained = a limit of the shell stopped the probe; refused = the shell rejected the syntax or command
    up front, so no limit was exercised; NOT contained = a harness cap or deadline had to stop it."""
    why = []
    if row["exit"] is None:
        why.append("deadline")
    sig = row.get("signal") or (row["exit"] - 128 if row["exit"] and row["exit"] > 128 else None)
    if sig:
        why.append(f"signal {sig}")
    if row["maxrss_mib"] > 1500:
        why.append(f"rss {row['maxrss_mib']} MiB")
    if row["output_bytes"] >= FSIZE_CAP * 0.9:
        why.append("output cap")
    if row["disk_bytes"] >= FSIZE_CAP * 0.9:
        why.append("disk cap")
    if why:
        verdict = "NOT contained"
    elif REFUSAL.search(row["stderr"]) and row["wall"] < 1.0 and row["exit"] != 0 or (
            row["exit"] == 0 and "command not allowed" in row["stderr"]):
        verdict, why = "refused", [row["stderr"].strip().splitlines()[-1][:60] if row["stderr"].strip() else ""]
    else:
        verdict = "contained"
    return {**row, "verdict": verdict, "why": ", ".join(why)}



# ---------------------------------------------------------------- conformance

def suite_conformance(tools: list[str], only: str, jobs: int) -> list[dict]:
    cases = [c for c in load_cases("conformance") if only in c.id]

    def one(c: Case) -> list[dict]:
        root, work, _, _ = new_workspace()
        ref = run_in("cpython", root, work, c.script, DEFAULT_POLICY, make_env())
        shutil.rmtree(root)
        rows = []
        for t in tools:
            root, work, _, _ = new_workspace()
            got = run_in(t, root, work, c.script, DEFAULT_POLICY, make_env())
            shutil.rmtree(root)
            rows.append({"suite": "conformance", "case": c.id, "tool": t, "verdict": classify(ref, got),
                         "exit": got.exit, "ref_exit": ref.exit, "wall": round(got.wall, 4),
                         "stdout": got.stdout.decode(errors="replace")[:2000],
                         "ref_stdout": ref.stdout.decode(errors="replace")[:2000],
                         "stderr": got.stderr.decode(errors="replace")[-500:]})
        return rows

    with cf.ThreadPoolExecutor(jobs) as ex:
        return [r for rows in ex.map(one, cases) for r in rows]


# ---------------------------------------------------------------- security

def suite_security(tools: list[str], only: str, jobs: int) -> list[dict]:
    cases = [c for c in load_cases("security") if only in c.id]

    def one(arg: tuple[Case, str]) -> dict:
        c, t = arg
        kind = c.name.split("-")[0]
        root, work, outside, token = new_workspace()
        env_token = "ENVTOKEN-" + secrets.token_hex(8)
        lst = Listener()
        script = (c.script.replace("@SECRET@", str(outside / "secret.txt"))
                  .replace("@OUTSIDE@", str(outside)).replace("@PORT@", str(lst.port)))
        before = snapshot(root)
        r = run_in(t, root, work, script, DEFAULT_POLICY, make_env({"HIDDEN_TOKEN": env_token}))
        time.sleep(0.05)
        lst.close()
        after = snapshot(root)
        text = r.stdout + r.stderr
        if kind == "read":
            escaped = token.encode() in text
        elif kind == "env":
            escaped = env_token.encode() in text
        elif kind in ("write", "exec"):
            escaped = before != after
        elif kind == "net":
            escaped = lst.hits > 0
        else:
            raise SystemExit(f"bad kind in {c.id}")
        shutil.rmtree(root, ignore_errors=True)
        return {"suite": "security", "case": c.id, "kind": kind, "tool": t,
                "verdict": "ESCAPED" if escaped else "blocked", "exit": r.exit,
                "stdout": r.stdout.decode(errors="replace")[:300], "stderr": r.stderr.decode(errors="replace")[-300:]}

    with cf.ThreadPoolExecutor(jobs) as ex:
        return list(ex.map(one, [(c, t) for c in cases for t in tools]))


# ---------------------------------------------------------------- policy

def load_policy_scenarios() -> list[tuple[str, str, list[Case]]]:
    """(scenario, policy JSON template, probes); a probe name is `allow|deny:NAME CHECK`."""
    out = []
    for f in sorted((CASES / "policy").glob("*.py")):
        header = next(line for line in f.read_text().splitlines() if line.startswith("# policy:"))
        out.append((f.stem, header.split(":", 1)[1].strip(), [c for c in load_cases("policy") if c.group == f.stem]))
    return out


def suite_policy(tools: list[str], only: str, jobs: int) -> list[dict]:
    jobs_list = []
    for scen, template, probes in load_policy_scenarios():
        for c in probes:
            if only in c.id:
                jobs_list += [(scen, template, c, t) for t in tools]

    def one(arg: tuple[str, str, Case, str]) -> dict:
        scen, template, c, t = arg
        expect, rest = c.name.split(":", 1)
        probe, check = rest.split(" ", 1)
        root, work, outside, token = new_workspace()
        (work / "secrets").mkdir()
        (work / "secrets/key.txt").write_text(token + "\n")
        (work / "out").mkdir()
        env_token = "ENVTOKEN-" + secrets.token_hex(8)
        http = HttpListener()
        subst = {"@PORT@": str(http.port), "@TOKEN@": token, "@ENVTOKEN@": env_token, "@WORK@": str(work),
                 "@SECRET@": str(outside / "secret.txt")}
        script = c.script
        for k, v in subst.items():
            template, script, check = template.replace(k, v), script.replace(k, v), check.replace(k, v)
        policy = json.loads(template)
        env = make_env({"HIDDEN_TOKEN": env_token})
        before = {str(q.relative_to(work)): q.read_bytes() for q in work.rglob("*") if q.is_file()}
        (root / "main.py").write_text(script)
        (root / "policy.json").write_text(json.dumps(policy))
        static = None
        cargv = adapter_argv(t, root / "policy.json", work, root / "main.py", check=True)
        if cargv:
            cr = execute(cargv, work, env)
            try:
                static = json.loads(cr.stdout)["status"]
            except (ValueError, KeyError):
                static = "error"
        r = execute(adapter_argv(t, root / "policy.json", work, root / "main.py", strict=True), work, env)
        time.sleep(0.05)
        happened = effect_happened(check, r, work, before, http.hits)
        http.close()
        shutil.rmtree(root, ignore_errors=True)
        if r.exit == 99 and b"unsupported" in r.stderr:
            verdict = "n/a"
        elif expect == "allow":
            verdict = "ok" if happened else "over-denied"
        else:
            verdict = "VIOLATED" if happened else "ok"
        return {"suite": "policy", "case": f"{scen}/{expect}:{probe}", "scenario": scen, "expect": expect,
                "tool": t, "verdict": verdict, "static": static, "exit": r.exit,
                "stdout": r.stdout[:300].decode(errors="replace"), "stderr": r.stderr[-300:].decode(errors="replace")}

    with cf.ThreadPoolExecutor(jobs) as ex:
        return list(ex.map(one, jobs_list))


# ---------------------------------------------------------------- resource

def suite_resource(tools: list[str], only: str, jobs: int) -> list[dict]:
    cases = [c for c in load_cases("resource") if only in c.id]

    def one(arg: tuple[Case, str]) -> dict:
        c, t = arg
        root, work, _, _ = new_workspace()
        r = run_in(t, root, work, c.script, DEFAULT_POLICY, make_env(), sandboxed=True)
        row = {"suite": "resource", "case": c.id, "tool": t, "exit": r.exit, "wall": round(r.wall, 2),
               "signal": r.signal, "maxrss_mib": r.maxrss_kb // 1024 if r.maxrss_kb >= 0 else -1,
               "output_bytes": r.extra["out_size"], "disk_bytes": dir_bytes(work),
               "stderr": r.stderr[-300:].decode(errors="replace")}
        shutil.rmtree(root, ignore_errors=True)
        return resource_verdict(row)

    with cf.ThreadPoolExecutor(max(1, jobs // 4)) as ex:  # heavy by design: few at a time
        return list(ex.map(one, [(c, t) for c in cases for t in tools]))


# ---------------------------------------------------------------- perf

def suite_perf(tools: list[str], only: str, jobs: int, repeats: int) -> list[dict]:
    cases = [c for c in load_cases("perf") if only in c.id]
    rows = []
    for c in cases:  # serial: timings must not compete
        ref = None
        for t in ["cpython"] + [t for t in tools if t != "cpython"]:
            walls, rss, last = [], [], None
            for _ in range(repeats):
                root, work, _, _ = new_workspace()
                last = run_in(t, root, work, c.script, DEFAULT_POLICY, make_env())
                walls.append(last.wall)
                rss.append(last.maxrss_kb)
                shutil.rmtree(root)
            if t == "cpython":
                ref = last
            if t not in tools:
                continue
            assert ref is not None and last is not None
            rows.append({"suite": "perf", "case": c.id, "tool": t, "median_s": round(statistics.median(walls), 4),
                         "min_s": round(min(walls), 4), "maxrss_mib": round(max(rss) / 1024, 1),
                         "verdict": classify(ref, last), "exit": last.exit,
                         "stderr": last.stderr[-300:].decode(errors="replace")})
    return rows


# ---------------------------------------------------------------- reporting

def versions() -> dict:
    def pkg(venv: str, name: str) -> str:
        try:
            out = subprocess.run([str(TOOLS_DIR / f"venv-{venv}/bin/python"), "-c",
                                  f"import importlib.metadata as m; print(m.version({name!r}))"],
                                 capture_output=True, text=True, timeout=30, check=False).stdout.strip()
            return out or "unknown"
        except OSError as e:
            return f"unknown ({e})"

    def py(venv: str) -> str:
        return subprocess.run([str(TOOLS_DIR / f"venv-{venv}/bin/python"), "--version"], capture_output=True,
                              text=True, check=False).stdout.strip()

    pyodide = json.loads((TOOLS_DIR / "pyodide/node_modules/pyodide/package.json").read_text())["version"]
    return {"cpython (oracle)": py("oracle"), "monty": "pydantic-monty " + pkg("monty", "pydantic-monty"),
            "ouros": f"ouros {pkg('ouros', 'ouros')} on {py('ouros')}",
            "smolagents": "smolagents " + pkg("smolagents", "smolagents"),
            "restrictedpython": "RestrictedPython " + pkg("restrictedpython", "RestrictedPython"),
            "pyodide": f"pyodide {pyodide} on node {subprocess.run(['node', '--version'], capture_output=True, text=True, check=False).stdout.strip()}",
            "host": platform.platform(), "date": time.strftime("%Y-%m-%d %H:%M")}


def summarize(rows: list[dict], tools: list[str]) -> str:
    lines = []
    suites = sorted({r["suite"] for r in rows}, key=["conformance", "security", "policy", "resource", "perf"].index)
    for s in suites:
        rs = [r for r in rows if r["suite"] == s]
        lines.append(f"\n## {s}\n")
        if s == "conformance":
            groups = sorted({r["case"].split("/")[0] for r in rs})
            lines.append("| tool | pass | loud fail | silent wrong | timeout | " + " | ".join(groups) + " |")
            lines.append("|---" * (5 + len(groups)) + "|")
            for t in tools:
                tr = [r for r in rs if r["tool"] == t]
                if not tr:
                    continue
                n = len(tr)
                cnt = {v: sum(r["verdict"] == v for r in tr) for v in ("pass", "loud", "silent", "timeout")}
                per = []
                for g in groups:
                    gr = [r for r in tr if r["case"].startswith(g + "/")]
                    per.append(f"{sum(r['verdict'] == 'pass' for r in gr)}/{len(gr)}")
                lines.append(f"| {t} | {cnt['pass']}/{n} ({100 * cnt['pass'] // n}%) | {cnt['loud']} | "
                             f"{cnt['silent']} | {cnt['timeout']} | " + " | ".join(per) + " |")
        elif s == "security":
            kinds = ["read", "write", "exec", "net", "env"]
            lines.append("| tool | blocked | " + " | ".join(f"{k} escapes" for k in kinds) + " |")
            lines.append("|---" * (2 + len(kinds)) + "|")
            for t in tools:
                tr = [r for r in rs if r["tool"] == t]
                if not tr:
                    continue
                esc = lambda k, tr=tr: [r["case"].split("/")[1] for r in tr if r["kind"] == k and r["verdict"] == "ESCAPED"]
                lines.append(f"| {t} | {sum(r['verdict'] == 'blocked' for r in tr)}/{len(tr)} | "
                             + " | ".join(", ".join(esc(k)) or "-" for k in kinds) + " |")
        elif s == "policy":
            scens = sorted({r["scenario"] for r in rs})
            lines.append("| scenario | " + " | ".join(tools) + " |")
            lines.append("|---" * (1 + len(tools)) + "|")
            for sc in scens:
                cells = []
                for t in tools:
                    tr = [r for r in rs if r["scenario"] == sc and r["tool"] == t]
                    if not tr:
                        cells.append("")
                        continue
                    if any(r["verdict"] == "n/a" for r in tr):
                        why = next(r["stderr"] for r in tr if r["verdict"] == "n/a").strip().splitlines()[0]
                        cells.append(f"n/a ({why.removeprefix('unsupported: ')[:70]})")
                        continue
                    al = [r for r in tr if r["expect"] == "allow"]
                    de = [r for r in tr if r["expect"] == "deny"]
                    viol = [r["case"].split(":", 1)[1] for r in de if r["verdict"] == "VIOLATED"]
                    over = [r["case"].split(":", 1)[1] for r in al if r["verdict"] != "ok"]
                    cell = (f"{'✅' if not viol and not over else ('❌' if viol else '⚠️')} "
                            f"deny {len(de) - len(viol)}/{len(de)}, allow {len(al) - len(over)}/{len(al)}")
                    if viol:
                        cell += f"; VIOLATED: {', '.join(viol)}"
                    if over:
                        cell += f"; over-denied: {', '.join(over)}"
                    cells.append(cell)
                lines.append(f"| {sc} | " + " | ".join(cells) + " |")
            st = [r for r in rs if r["static"] and r["verdict"] != "n/a"]
            if st:
                lines.append("\nStatic pre-check (tools with one), counted over probes whose policy is expressible:\n")
                for t in sorted({r["tool"] for r in st}):
                    for e in ("deny", "allow"):
                        tr = [r for r in st if r["tool"] == t and r["expect"] == e]
                        c = {k: sum(r["static"] == k for r in tr) for k in ("denied", "indeterminate", "allowed")}
                        lines.append(f"- {t}, {e} probes: denied {c['denied']}, indeterminate {c['indeterminate']}, "
                                     f"allowed {c['allowed']} (of {len(tr)})")
                bad = [f"{r['tool']} {r['case']}" for r in st if r["expect"] == "deny" and r["static"] == "allowed"]
                if bad:
                    lines.append(f"- deny probes the static check *allowed* (the run still enforced the policy): {', '.join(bad)}")
        elif s == "resource":
            cases = sorted({r["case"] for r in rs})
            lines.append("| case | " + " | ".join(tools) + " |")
            lines.append("|---" * (1 + len(tools)) + "|")
            for c in cases:
                cells = []
                for t in tools:
                    r = next((r for r in rs if r["case"] == c and r["tool"] == t), None)
                    cells.append("" if not r else {"contained": "ok ", "refused": "refused ", "NOT contained": "✗ "}[r["verdict"]] +
                                 f"{r['wall']}s " + (f"{r['maxrss_mib']}MiB" if r["maxrss_mib"] >= 0 else "?MiB") + (f" ({r['why']})" if r["why"] else ""))
                lines.append(f"| {c.split('/')[1]} | " + " | ".join(cells) + " |")
        elif s == "perf":
            cases = sorted({r["case"] for r in rs}, key=lambda c: [r["case"] for r in rs].index(c))
            lines.append("| case | " + " | ".join(tools) + " |")
            lines.append("|---" * (1 + len(tools)) + "|")
            for c in cases:
                cells = []
                for t in tools:
                    r = next((r for r in rs if r["case"] == c and r["tool"] == t), None)
                    cells.append("" if not r else f"{r['median_s'] * 1000:.0f}ms {r['maxrss_mib']:.0f}MiB"
                                 + ("" if r["verdict"] == "pass" else f" ({r['verdict']})"))
                lines.append(f"| {c.split('/')[1]} | " + " | ".join(cells) + " |")
            lines.append("\nCell: median wall time over the repeats, peak RSS; a non-`pass` verdict means the output "
                         "differed from CPython, so the time is not comparable.")
    return "\n".join(lines) + "\n"


def selfcheck(jobs: int) -> int:
    """Validate the instruments: cpython is the known positive, null the known negative."""
    ok = True
    conf = suite_conformance(["cpython"], "", jobs)
    bad = [r["case"] for r in conf if r["verdict"] != "pass"]
    print(f"conformance cpython-vs-cpython: {len(conf) - len(bad)}/{len(conf)} pass", "✅" if not bad else f"❌ {bad}")
    ok &= not bad
    sec = suite_security(["cpython", "null"], "", jobs)
    optional = {"read-pyodide-js-fs", "exec-pyodide-js-child-process", "exec-pyodide-ffi-constructor",
                "net-pyodide-js-fetch", "exec-ctypes-system"}
    missed = [r["case"] for r in sec if r["tool"] == "cpython" and r["verdict"] == "blocked"
              and r["case"].split("/")[1] not in optional]
    leaked = [r["case"] for r in sec if r["tool"] == "null" and r["verdict"] != "blocked"]
    print(f"security cpython escapes (known positive): missed {missed or 'none'}", "✅" if not missed else "❌")
    print(f"security null blocks (known negative): leaked {leaked or 'none'}", "✅" if not leaked else "❌")
    ok &= not missed and not leaked
    pol = suite_policy(["cpython", "null"], "", jobs)
    missed = [r["case"] for r in pol if r["tool"] == "cpython" and r["expect"] == "deny" and r["verdict"] == "ok"]
    missed += [r["case"] for r in pol if r["tool"] == "cpython" and r["expect"] == "allow" and r["verdict"] != "ok"]
    print(f"policy cpython shows every effect (known positive): missed {missed or 'none'}", "✅" if not missed else "❌")
    shown = [r["case"] for r in pol if r["tool"] == "null" and r["expect"] == "deny" and r["verdict"] != "ok"]
    shown += [r["case"] for r in pol if r["tool"] == "null" and r["expect"] == "allow" and r["verdict"] == "ok"]
    print(f"policy null shows no effect (known negative): shown {shown or 'none'}", "✅" if not shown else "❌")
    ok &= not missed and not shown
    res = suite_resource(["cpython", "null"], "", jobs)
    bad = [r["case"] for r in res if r["tool"] == "null" and r["verdict"] != "contained"]
    print(f"resource null contained (known negative): not contained {bad or 'none'}", "✅" if not bad else "❌")
    held = [r["case"] for r in res if r["tool"] == "cpython" and r["verdict"] != "NOT contained"]
    print(f"resource cpython not contained (known positive): contained {held or 'none'}", "✅" if not held else "❌")
    ok &= not bad and not held
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("suite", choices=["conformance", "security", "policy", "resource", "perf", "all", "selfcheck"])
    ap.add_argument("--tools", default=",".join(ALL_TOOLS))
    ap.add_argument("--only", default="", help="substring filter on case ids")
    ap.add_argument("--json", type=Path, help="write raw rows + versions as JSON")
    ap.add_argument("--report", type=Path, help="write the Markdown summary here")
    ap.add_argument("-n", type=int, default=5, help="perf repeats")
    ap.add_argument("-j", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--from-json", type=Path, help="re-render the report from a previous --json file (suite: all)")
    a = ap.parse_args()
    if a.from_json:
        data = json.loads(a.from_json.read_text())
        rows = [resource_verdict(r) if r["suite"] == "resource" else r for r in data["rows"]]
        md = "# Python sandbox benchmark results\n\n" + "\n".join(f"- {k}: {val}" for k, val in data["versions"].items())
        md += "\n" + summarize(rows, a.tools.split(","))
        if a.json:
            a.json.write_text(json.dumps({"versions": data["versions"], "rows": rows}, indent=1))
        (a.report.write_text(md) if a.report else print(md))
        return 0
    if a.suite == "selfcheck":
        return selfcheck(a.j)
    tools = a.tools.split(",")
    rows: list[dict] = []
    for s in (["conformance", "security", "policy", "resource", "perf"] if a.suite == "all" else [a.suite]):
        print(f"running {s} …", file=sys.stderr)
        if s == "perf":
            rows += suite_perf(tools, a.only, a.j, a.n)
        else:
            rows += globals()[f"suite_{s}"](tools, a.only, a.j)
    v = versions()
    md = "# Python sandbox benchmark results\n\n" + "\n".join(f"- {k}: {val}" for k, val in v.items()) + "\n" + summarize(rows, tools)
    if a.json:
        a.json.write_text(json.dumps({"versions": v, "rows": rows}, indent=1))
    if a.report:
        a.report.write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
