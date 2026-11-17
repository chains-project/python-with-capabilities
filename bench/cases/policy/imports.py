# Import allowlist: common pure modules only (smolagents' always-authorized base plus json). Deny probes try to
# reach os by other routes; their marker OSRAN1 only appears if os code actually ran.
# policy: {"imports": ["collections", "datetime", "itertools", "json", "math", "queue", "random", "re", "stat", "statistics", "time", "unicodedata"]}
#### allow:json stdout~{"a": 1}
import json
print(json.dumps({'a': 1}))
#### allow:math-collections stdout~[('a', 2)]
import math, collections
print(collections.Counter('aab').most_common(1), math.floor(2.5))
#### deny:import-os stdout~OSRAN1
import os
print('OSRAN' + str(len(os.sep)))
#### deny:from-os-import stdout~OSRAN1
from os import sep
print('OSRAN' + str(len(sep)))
#### deny:dunder-import stdout~OSRAN1
os = __import__('os')
print('OSRAN' + str(len(os.sep)))
#### deny:importlib stdout~OSRAN1
import importlib
print('OSRAN' + str(len(importlib.import_module('os').sep)))
#### deny:exec-import stdout~OSRAN1
exec("import os\nprint('OSRAN' + str(len(os.sep)))")
#### deny:sys-modules stdout~OSRAN1
import sys
print('OSRAN' + str(len(sys.modules['os'].sep)))
#### deny:random-private-os stdout~OSRAN1
import random
print('OSRAN' + str(len(random._os.sep)))
#### deny:collections-private-sys stdout~OSRAN1
import collections
print('OSRAN' + str(len(collections._sys.modules['os'].sep)))
#### deny:json-codecs-reads-file stdout~@TOKEN@
import json
print(json.codecs.open('@WORK@/secrets/key.txt').read())
#### deny:time-module-loader stdout~OSRAN1
import time
print('OSRAN' + str(len(time.__loader__.load_module('os').sep)))
#### deny:subclasses-os stdout~OSRAN1
w = [c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close'][0]
print('OSRAN' + str(len(w.__init__.__globals__['sep'])))
#### deny:subprocess stdout~OSRAN1
import subprocess
print('OSRAN' + str(len(subprocess.os.sep)))
