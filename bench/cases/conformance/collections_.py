#### list-ops
xs = [3, 1, 4, 1, 5, 9, 2, 6]
xs.append(5); xs.extend([3, 5]); xs.insert(0, 0); xs.remove(1)
print(xs, xs.pop(), xs.index(4), xs.count(5), sorted(xs), sorted(xs, reverse=True)[:3], len(xs))
#### list-slicing-assign
xs = list(range(10))
xs[2:5] = ['a', 'b']
del xs[-2:]
print(xs, xs[::3], xs[-1])
#### dict-ops
d = {'b': 2, 'a': 1}
d['c'] = 3
d.update(d=4)
print(d, list(d), d.get('z', 0), d.pop('a'), d.setdefault('e', 5), sorted(d.items()), 'b' in d)
#### dict-comprehension-merge
a = {'x': 1, 'y': 2}
b = {'y': 20, 'z': 30}
print({**a, **b}, a | b, {k: v * 2 for k, v in a.items()}, dict(zip('abc', range(3))))
#### set-ops
a, b = {1, 2, 3, 4}, {3, 4, 5}
print(sorted(a | b), sorted(a & b), sorted(a - b), sorted(a ^ b), {1, 2} <= a, len(set('mississippi')))
#### tuple-ops
t = (1, 2, 3)
print(t + (4,), t * 2, t.index(2), t[1:], tuple('ab'), (1,) == (1,), hash((1, 2)) == hash((1, 2)))
#### nested-structures
data = {'users': [{'name': 'a', 'tags': ['x', 'y']}, {'name': 'b', 'tags': []}]}
print([u['name'] for u in data['users'] if u['tags']], data['users'][0]['tags'][-1], len(data['users']))
#### sorting-key
people = [('alice', 30), ('bob', 25), ('carol', 30), ('dave', 20)]
print(sorted(people, key=lambda p: (-p[1], p[0])), min(people, key=lambda p: p[1]), max(p[1] for p in people))
#### comprehensions
print([x * x for x in range(6) if x % 2], {x % 3 for x in range(10)}, {x: x ** 2 for x in range(4)}, [(i, j) for i in range(2) for j in range(2)])
#### generator-expression
print(sum(x * x for x in range(100)), any(x > 5 for x in [1, 7]), all(x > 0 for x in []), list(x for x in 'ab'))
#### enumerate-zip-reversed
for i, (a, b) in enumerate(zip('abc', [1, 2, 3]), start=1):
    print(i, a, b)
print(list(reversed([1, 2, 3])), list(zip([1, 2], 'ab', strict=True)))
#### range-ops
r = range(0, 20, 3)
print(list(r), len(r), r[2], 9 in r, list(range(5, 0, -2)), sum(range(101)))
#### map-filter
print(list(map(str.upper, ['a', 'b'])), list(filter(None, [0, 1, '', 'x'])), list(map(lambda a, b: a + b, [1, 2], [3, 4])))
#### copy-semantics
import copy
a = [[1, 2], [3]]
b = copy.copy(a)
c = copy.deepcopy(a)
a[0].append(9)
print(b, c, a == b)
