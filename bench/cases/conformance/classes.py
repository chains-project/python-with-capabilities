#### class-basic
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def norm2(self):
        return self.x ** 2 + self.y ** 2
    def __repr__(self):
        return f'Point({self.x}, {self.y})'
p = Point(3, 4)
print(p, p.norm2(), p.x)
#### inheritance-super
class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self):
        return f'{self.name} makes a sound'
class Dog(Animal):
    def speak(self):
        return super().speak() + ' (woof)'
print(Dog('rex').speak(), isinstance(Dog('a'), Animal), issubclass(Dog, Animal))
#### dunder-methods
class V:
    def __init__(self, *c):
        self.c = c
    def __add__(self, o):
        return V(*(a + b for a, b in zip(self.c, o.c)))
    def __eq__(self, o):
        return self.c == o.c
    def __len__(self):
        return len(self.c)
    def __getitem__(self, i):
        return self.c[i]
    def __repr__(self):
        return f'V{self.c}'
print(V(1, 2) + V(3, 4), V(1) == V(1), len(V(1, 2, 3)), V(5, 6)[1], list(V(7, 8)))
#### class-attributes-and-classmethod
class Counter:
    total = 0
    def __init__(self):
        Counter.total += 1
    @classmethod
    def make(cls):
        return cls()
    @staticmethod
    def describe():
        return 'counter'
Counter(); Counter.make()
print(Counter.total, Counter.describe())
#### property
class Temp:
    def __init__(self, c):
        self._c = c
    @property
    def f(self):
        return self._c * 9 / 5 + 32
    @f.setter
    def f(self, v):
        self._c = (v - 32) * 5 / 9
t = Temp(100)
t.f = 32
print(Temp(100).f, t._c)
#### dataclass
from dataclasses import dataclass, field
@dataclass(order=True)
class Item:
    price: float
    name: str = 'x'
    tags: list = field(default_factory=list)
a = Item(2.5, 'pen')
print(a, a == Item(2.5, 'pen'), sorted([Item(3), Item(1)])[0].price)
#### enum
from enum import Enum, auto
class Color(Enum):
    RED = auto()
    GREEN = auto()
print(Color.RED, Color.GREEN.value, Color['RED'] is Color.RED, [c.name for c in Color])
#### iterator-protocol
class Squares:
    def __init__(self, n):
        self.i, self.n = 0, n
    def __iter__(self):
        return self
    def __next__(self):
        if self.i >= self.n:
            raise StopIteration
        self.i += 1
        return self.i ** 2
print(list(Squares(4)), sum(Squares(3)))
#### context-manager
class Ctx:
    def __enter__(self):
        print('enter')
        return 'value'
    def __exit__(self, *exc):
        print('exit', exc[0].__name__ if exc[0] else None)
        return True
with Ctx() as v:
    print(v)
    raise ValueError('swallowed')
print('after')
#### str-and-hash
class K:
    def __init__(self, k):
        self.k = k
    def __hash__(self):
        return hash(self.k)
    def __eq__(self, o):
        return self.k == o.k
    def __str__(self):
        return f'K<{self.k}>'
print(len({K(1), K(1), K(2)}), str(K(3)), f'{K(4)}')
#### namedtuple
from collections import namedtuple
P = namedtuple('P', 'x y')
p = P(1, y=2)
print(p, p.x + p.y, p._replace(x=5), p._asdict())
