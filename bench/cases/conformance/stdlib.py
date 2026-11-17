#### json
import json
data = {'name': 'x', 'n': [1, 2.5, None, True], 'nested': {'k': 'é'}}
s = json.dumps(data, sort_keys=True)
print(s, json.loads(s) == data, json.dumps(data, indent=2).count('\n'), json.dumps('é', ensure_ascii=False))
#### re
import re
text = 'Order 66 shipped on 2026-11-17 to bob@example.com; order 7 pending'
print(re.findall(r'\d+', text), re.search(r'(\d{4})-(\d\d)-(\d\d)', text).groups(), re.sub(r'(?i)order', 'ORD', text)[:12])
print(re.split(r'[;,]\s*', 'a, b;c'), bool(re.fullmatch(r'[\w.]+@[\w.]+', 'bob@example.com')), re.compile(r'(?P<w>\w+)@').search(text).group('w'))
#### math
import math
print(math.sqrt(16), math.floor(-2.5), math.ceil(2.1), math.gcd(12, 18), math.factorial(10), round(math.pi, 5), math.isclose(0.1 + 0.2, 0.3), math.inf > 1e308)
#### collections
from collections import Counter, defaultdict, deque, OrderedDict
c = Counter('mississippi')
d = defaultdict(list)
for k, v in [('a', 1), ('b', 2), ('a', 3)]:
    d[k].append(v)
q = deque([1, 2, 3], maxlen=3)
q.append(4)
print(c.most_common(2), dict(d), list(q), q.popleft(), list(OrderedDict(b=1, a=2)))
#### itertools
import itertools
print(list(itertools.chain([1], [2, 3])), list(itertools.combinations('abc', 2)), list(itertools.permutations([1, 2])),
      list(itertools.islice(itertools.count(5), 3)), [(k, len(list(g))) for k, g in itertools.groupby('aabbbc')],
      list(itertools.accumulate([1, 2, 3])), list(itertools.product('ab', repeat=2))[:3])
#### datetime
from datetime import date, datetime, timedelta
d = date(2026, 11, 17)
print(d.isoformat(), d.weekday(), d + timedelta(days=30), (date(2027, 1, 1) - d).days, d.strftime('%A %d %B %Y'))
print(datetime(2026, 1, 2, 3, 4, 5).isoformat(), datetime.fromisoformat('2026-11-17T08:30:00').hour)
#### random-seeded
import random
random.seed(42)
print(random.randint(1, 100), random.choice('abcdef'), random.random() < 1, sorted(random.sample(range(100), 3)))
#### statistics
import statistics
xs = [2, 4, 4, 4, 5, 5, 7, 9]
print(statistics.mean(xs), statistics.median(xs), statistics.mode(xs), statistics.pstdev(xs))
#### heapq-bisect
import heapq, bisect
h = [5, 1, 8, 3]
heapq.heapify(h)
print(heapq.heappop(h), heapq.nsmallest(2, [9, 4, 7, 1]), bisect.bisect_left([1, 3, 5, 7], 5))
#### decimal-fractions
from decimal import Decimal
from fractions import Fraction
print(Decimal('0.1') + Decimal('0.2'), Fraction(1, 3) + Fraction(1, 6), Decimal(10) / Decimal(3))
#### string-module-textwrap
import string, textwrap
print(string.ascii_lowercase[:5], string.digits, textwrap.wrap('the quick brown fox jumps over', width=10), textwrap.dedent('  a\n  b'))
#### typing-annotations
from typing import Optional
def f(x: int, y: Optional[str] = None) -> list[int]:
    return [x]
print(f(1), f.__annotations__['x'].__name__)
#### operator-module
import operator
print(sorted([(1, 'b'), (0, 'a')], key=operator.itemgetter(1)), operator.add(2, 3), list(map(operator.mul, [1, 2], [3, 4])))
#### unicodedata
import unicodedata
print(unicodedata.name('é'), unicodedata.normalize('NFD', 'é').encode(), unicodedata.category('A'))
#### asyncio
import asyncio
async def work(n):
    await asyncio.sleep(0)
    return n * 2
async def main():
    return await asyncio.gather(*(work(i) for i in range(3)))
print(asyncio.run(main()))
#### host-function-call
print(lookup('apple'), lookup('banana'), lookup('kiwi'))
