#### defaults-kwargs
def f(a, b=2, *args, c=3, **kw):
    return a, b, args, c, sorted(kw.items())
print(f(1), f(1, 5, 6, 7, c=8, z=9, y=0))
#### keyword-only-positional-only
def g(a, /, b, *, c):
    return a + b + c
print(g(1, 2, c=3), g(1, b=2, c=3))
#### closures
def make_adders():
    return [lambda x, i=i: x + i for i in range(3)]
print([f(10) for f in make_adders()])
#### recursion
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)
print([fib(i) for i in range(15)])
#### decorators
def twice(fn):
    def wrapper(*a):
        return fn(*a) * 2
    return wrapper
@twice
def three():
    return 3
print(three())
#### decorator-with-args-and-wraps
import functools
def tag(name):
    def deco(fn):
        @functools.wraps(fn)
        def inner(*a, **k):
            return f'<{name}>{fn(*a, **k)}</{name}>'
        return inner
    return deco
@tag('b')
def hello(who):
    """greets"""
    return 'hi ' + who
print(hello('you'), hello.__name__, hello.__doc__)
#### generators
def countdown(n):
    while n > 0:
        yield n
        n -= 1
print(list(countdown(4)), next(iter(countdown(2))))
#### generator-send-yield-from
def inner():
    x = yield 1
    yield x * 2
def outer():
    yield from inner()
    yield 'done'
g = outer()
print(next(g), g.send(21), next(g))
#### star-unpacking-calls
def h(a, b, c):
    return a * 100 + b * 10 + c
args = [1, 2]
print(h(*args, 3), h(**{'a': 1, 'b': 2, 'c': 3}), max(*[3, 7, 2]))
#### functools-tools
import functools
print(functools.reduce(lambda a, b: a * b, range(1, 6)), functools.partial(int, base=2)('101'))
@functools.lru_cache(maxsize=None)
def slow(n):
    return n if n < 2 else slow(n - 1) + slow(n - 2)
print(slow(80))
#### higher-order
def compose(*fs):
    def h(x):
        for f in reversed(fs):
            x = f(x)
        return x
    return h
print(compose(str, lambda x: x + 1, abs)(-5))
#### lambda-sorting-builtins
print(sorted(['b', 'A', 'c'], key=str.lower), min([3, 1, 2]), max('hello'), sum([0.5] * 4), abs(-2.5))
