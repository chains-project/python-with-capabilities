#!/usr/bin/env bash
# Create the pinned runtimes under bench/.tools/: one virtualenv per tool (they need different Pythons) and Pyodide.
# Requires: uv, node (>=22), npm, git.
set -euo pipefail
cd "$(dirname "$0")"
T=.tools
mkdir -p "$T"

venv() { # name python-version [package]
  [ -x "$T/venv-$1/bin/python" ] || uv venv -q --python "$2" "$T/venv-$1"
  [ -z "${3:-}" ] || uv pip install -q --python "$T/venv-$1/bin/python" "$3"
}
venv oracle 3.14                              # CPython, the reference and known-positive control
venv monty 3.14 pydantic-monty==1.6.0
venv ouros 3.13 ouros==0.0.7                  # no cp314 wheel
venv smolagents 3.14 smolagents==1.26.0
venv restrictedpython 3.14 RestrictedPython==9.0

mkdir -p "$T/pyodide" && (cd "$T/pyodide" && { [ -f package.json ] || npm init -y >/dev/null; } && npm i -s pyodide@314.0.8)

# Source clones, used as evidence by QUALITATIVE.md (not needed to run the benchmark).
mkdir -p "$T/src"
for r in pydantic/monty parcadei/ouros huggingface/smolagents zopefoundation/RestrictedPython; do
  [ -d "$T/src/${r#*/}" ] || git clone -q --depth 1 "https://github.com/$r" "$T/src/${r#*/}"
done
