# Performance tasks: pure computation, the same output as CPython expected.
#### startup
pass
#### loop-sum-1m
s = 0
for i in range(1_000_000):
    s += i * i
print(s)
#### fib-recursive-25
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)
print(fib(25))
#### string-build-100k
print(len(''.join(str(i) for i in range(100_000))))
#### dict-ops-200k
d = {}
for i in range(200_000):
    d[i % 1000] = d.get(i % 1000, 0) + i
print(sum(d.values()))
#### sort-200k
import random
random.seed(1)
xs = [random.random() for _ in range(200_000)]
xs.sort()
print(round(xs[100_000], 6))
#### json-roundtrip
import json
data = [{'id': i, 'name': f'n{i}', 'tags': ['a', 'b'], 'v': i / 3} for i in range(20_000)]
print(len(json.loads(json.dumps(data))))
#### regex-findall-1mb
import re
text = 'word 123 other 4567 ' * 50_000
print(len(re.findall(r'\d+', text)))
#### class-method-calls-300k
class C:
    def __init__(self):
        self.n = 0
    def inc(self):
        self.n += 1
c = C()
for _ in range(300_000):
    c.inc()
print(c.n)
