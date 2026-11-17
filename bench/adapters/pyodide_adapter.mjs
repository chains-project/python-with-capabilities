// Pyodide (CPython compiled to WebAssembly) in Node: grants map to globals, NODEFS mounts and the Emscripten env.
// Usage: node pyodide_adapter.mjs [--strict] POLICY.json WORKDIR SCRIPT.py   (see POLICY.md)
// `jsglobals: {}` hides the Node global object from Python's `js` module: the documented way to narrow the JS side.
import { readFileSync } from 'node:fs'
import { join, normalize } from 'node:path'
import { createRequire } from 'node:module'
const require = createRequire(new URL('../.tools/pyodide/package.json', import.meta.url))
const { loadPyodide } = require('pyodide')

let args = process.argv.slice(2)
const strict = args[0] === '--strict'
if (strict) args = args.slice(1)
const [policyPath, workdir, scriptPath] = args
const policy = JSON.parse(readFileSync(policyPath, 'utf8'))
const code = readFileSync(scriptPath, 'utf8')
const unsupported = (why) => {
  if (!strict) return
  process.stderr.write(`unsupported: ${why}\n`)
  process.exit(99)
}
if ('imports' in policy) unsupported('no import allowlist: every bundled module is importable')
for (const [rel, mode] of Object.entries(policy.fs ?? {})) {
  if (mode !== 'rw') unsupported(`NODEFS mounts have no read-only mode (grant ${rel}:${mode})`)
}

const catalog = {
  lookup: (key) => String({ apple: 3, banana: 5 }[key] ?? 0),
  admin_reset: () => { process.stdout.write('ADMIN' + 'RAN\n'); return 'done' },
}
const out = (s) => process.stdout.write(s + '\n')
const err = (s) => process.stderr.write(s + '\n')
const py = await loadPyodide({ jsglobals: {}, env: policy.env ?? {}, stdout: out, stderr: err })
for (const name of policy.functions ?? []) py.globals.set(name, catalog[name])
if (policy.fs) {
  py.FS.mkdirTree('/work')
  for (const rel of Object.keys(policy.fs)) {
    const mnt = normalize(join('/work', rel))
    py.FS.mkdirTree(mnt)
    py.FS.mount(py.FS.filesystems.NODEFS, { root: join(workdir, rel) }, mnt)
  }
  py.runPython("import os; os.chdir('/work')")
}
const timer = setTimeout(() => { err('timeout: 10 s'); process.exit(124) }, 10000)
try {
  await py.runPythonAsync(code)
} catch (e) {
  err(String(e.message ?? e).trim().split('\n').slice(-3).join('\n'))
  process.exitCode = 1
}
clearTimeout(timer)
process.exit(process.exitCode ?? 0)
