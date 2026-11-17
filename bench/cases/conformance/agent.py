#### agent-csv-like-aggregation
rows = """name,dept,salary
alice,eng,120
bob,eng,100
carol,ops,90
dave,ops,95""".splitlines()
header, *body = [r.split(',') for r in rows]
by = {}
for name, dept, sal in body:
    by.setdefault(dept, []).append(int(sal))
for dept, sals in sorted(by.items()):
    print(f'{dept}: n={len(sals)} avg={sum(sals) / len(sals):.1f} max={max(sals)}')
#### agent-json-transform
import json
payload = json.loads('{"items": [{"id": 1, "price": 9.99, "qty": 3}, {"id": 2, "price": 0.5, "qty": 10}]}')
total = sum(i['price'] * i['qty'] for i in payload['items'])
print(json.dumps({'count': len(payload['items']), 'total': round(total, 2), 'ids': [i['id'] for i in payload['items']]}))
#### agent-text-stats
from collections import Counter
import re
text = 'The cat sat on the mat. The dog sat on the log.'
words = re.findall(r'[a-z]+', text.lower())
print(len(words), Counter(words).most_common(3), sorted(set(words))[:4])
#### agent-tool-loop
results = {}
for fruit in ['apple', 'banana', 'cherry']:
    results[fruit] = int(lookup(fruit))
best = max(results, key=results.get)
print(results, best, sum(results.values()))
#### agent-retry-with-errors
attempts = []
def flaky(i):
    if i < 2:
        raise ConnectionError(f'try {i}')
    return 'ok'
for i in range(5):
    try:
        r = flaky(i)
        break
    except ConnectionError as e:
        attempts.append(str(e))
print(r, attempts)
#### agent-date-report
from datetime import date, timedelta
start = date(2026, 11, 1)
days = [start + timedelta(days=i) for i in range(0, 30, 7)]
print([d.isoformat() for d in days], sum(1 for d in days if d.weekday() < 5))
#### agent-table-format
rows = [('apple', 3, 0.5), ('banana', 12, 0.25), ('kiwi', 7, 1.0)]
print(f"{'item':<8}{'qty':>5}{'cost':>8}")
for name, q, p in rows:
    print(f'{name:<8}{q:>5}{q * p:>8.2f}')
#### agent-final-dict
summary = {'status': 'done', 'steps': 3, 'notes': None}
print(summary)
