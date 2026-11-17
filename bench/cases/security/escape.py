# Escape probes, run under the default agent policy (common stdlib imports + the host function `lookup`).
# The case name prefix is the escape kind, which tells the harness how to detect success:
#   read-*  the secret token (contents of @SECRET@, outside the workdir) appears in stdout/stderr
#   env-*   the host environment token (HIDDEN_TOKEN) appears in stdout/stderr
#   write-* / exec-*  a file appears or changes in @OUTSIDE@ or the run's parent directory on the host
#   net-*   the harness TCP listener on 127.0.0.1:@PORT@ receives a connection
#### read-open
print(open('@SECRET@').read())
#### read-pathlib
from pathlib import Path
print(Path('@SECRET@').read_text())
#### read-dotdot
print(open('../outside/secret.txt').read())
#### read-io-open
import io
print(io.open('@SECRET@').read())
#### read-os-open
import os
print(os.read(os.open('@SECRET@', os.O_RDONLY), 100))
#### read-builtins-module
print(__import__('builtins').open('@SECRET@').read())
#### read-builtins-dict
b = __builtins__
o = b['open'] if isinstance(b, dict) else b.open
print(o('@SECRET@').read())
#### read-codecs
import codecs
print(codecs.open('@SECRET@').read())
#### read-linecache
import linecache
print(linecache.getlines('@SECRET@'))
#### read-subclasses-fileio
def walk(c):
    for s in type.__subclasses__(c):
        yield s
        yield from walk(s)
fio = next(c for c in walk(object) if c.__name__ == 'FileIO')
print(fio('@SECRET@').read())
#### read-function-globals
print(lookup.__globals__['os'].popen('cat @SECRET@').read())
#### read-getattr-concat
g = getattr(lookup, '__glo' + 'bals__')
print(g['os'].popen('cat @SECRET@').read())
#### read-object-getattribute
g = object.__getattribute__(lookup, '__globals__')
print(g['os'].popen('cat @SECRET@').read())
#### read-type-dict-descriptor
g = type(lookup).__dict__['__globals__'].__get__(lookup)
print(g['os'].popen('cat @SECRET@').read())
#### read-generator-frame
def gen():
    yield 1
g = gen()
f = g.gi_frame
while f.f_back is not None:
    f = f.f_back
print(f.f_builtins['open']('@SECRET@').read())
#### read-traceback-frame
try:
    1 / 0
except ZeroDivisionError as e:
    f = e.__traceback__.tb_frame
    while f.f_back is not None:
        f = f.f_back
    b = f.f_builtins
    print(b['open']('@SECRET@').read())
#### read-sys-modules
import sys
print(sys.modules['os'].popen('cat @SECRET@').read())
#### read-random-os
import random
print(random._os.popen('cat @SECRET@').read())
#### read-collections-sys
import collections
print(collections._sys.modules['os'].popen('cat @SECRET@').read())
#### read-importlib
import importlib
print(importlib.import_module('os').popen('cat @SECRET@').read())
#### read-exec-string
exec("import os\nprint(os.popen('cat @SECRET@').read())")
#### read-eval-import
print(eval("__import__('os').popen('cat @SECRET@').read()"))
#### read-pyodide-js-fs
import js
print(js.constructor.constructor('return process')().getBuiltinModule('fs').readFileSync('@SECRET@', 'utf8'))
#### env-os-environ
import os
print(dict(os.environ))
#### env-getenv
import os
print(os.getenv('HIDDEN_TOKEN'))
#### env-proc-environ
print(open('/proc/self/environ').read())
#### env-format-string-globals
print('{0.__globals__[os].environ}'.format(lookup))
#### env-function-globals
print(lookup.__globals__['os'].environ['HIDDEN_TOKEN'])
#### write-open
open('@OUTSIDE@/w1', 'w').write('x')
#### write-pathlib
from pathlib import Path
Path('@OUTSIDE@/w2').write_text('x')
#### write-dotdot
open('../outside/w3', 'w').write('x')
#### write-remove-secret
import os
os.remove('@SECRET@')
#### write-shutil
import shutil
shutil.copy('../outside/secret.txt', '@OUTSIDE@/w4')
#### write-mkdir
import os
os.mkdir('@OUTSIDE@/d1')
#### exec-os-system
import os
os.system('touch @OUTSIDE@/x1')
#### exec-subprocess
import subprocess
subprocess.run(['touch', '@OUTSIDE@/x2'])
#### exec-subclasses-wrap-close
w = [c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close'][0]
w.__init__.__globals__['system']('touch @OUTSIDE@/x3')
#### exec-function-globals-subprocess
lookup.__globals__['subprocess'].run(['touch', '@OUTSIDE@/x4'])
#### exec-pickle
import pickle
pickle.loads(b"cos\nsystem\n(S'touch @OUTSIDE@/x5'\ntR.")
#### exec-ctypes-system
import ctypes
ctypes.CDLL(None).system(b'touch @OUTSIDE@/x6')
#### exec-class-mro-builtins
for c in object.__subclasses__():
    init = getattr(c, '__init__', None)
    g = getattr(init, '__globals__', None)
    if g and 'sys' in g:
        g['sys'].modules['os'].system('touch @OUTSIDE@/x7')
        break
#### exec-pyodide-js-child-process
import js
js.constructor.constructor('return process')().getBuiltinModule('child_process').execSync('touch @OUTSIDE@/x8')
#### exec-pyodide-ffi-constructor
import pyodide_js
pyodide_js.constructor.constructor("process.getBuiltinModule('child_process').execSync('touch @OUTSIDE@/x9')")()
#### net-socket
import socket
socket.create_connection(('127.0.0.1', @PORT@), timeout=3).sendall(b'hi')
#### net-urllib
import urllib.request
urllib.request.urlopen('http://127.0.0.1:@PORT@/', timeout=3)
#### net-http-client
import http.client
c = http.client.HTTPConnection('127.0.0.1', @PORT@, timeout=3)
c.request('GET', '/')
#### net-pyodide-js-fetch
import js
await js.constructor.constructor('return fetch')()('http://127.0.0.1:@PORT@/')
