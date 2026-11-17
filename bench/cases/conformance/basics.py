#### int-arith
print(7 * 6, 17 // 5, 17 % 5, -17 // 5, -17 % 5, 2 ** 100, divmod(17, 5), abs(-3))
#### float-arith
print(0.1 + 0.2, 1 / 3, round(2.675, 2), round(2.5), round(3.5), 1e300 * 10, float('nan') == float('nan'))
#### int-float-conversions
print(int('42'), int('ff', 16), int(3.9), float('1.5'), int(-3.9), bin(10), hex(255), oct(8))
#### bool-logic
print(True + True, not 0, 0 or 'x', '' and 'y', None is None, 1 < 2 < 3, 3 > 2 == 2)
#### comparison-chains
x = 5
print(1 < x <= 5, 0 < x < 3, x == 5.0, [1, 2] < [1, 3], (1, 'a') < (1, 'b'))
#### walrus
data = [1, 5, 9, 12]
if (n := len(data)) > 3:
    print(f'{n} items')
print([y for x in data if (y := x * 2) > 10])
#### none-and-identity
a = [1]
b = a
print(a is b, a == [1], a is [1], None == 0)
#### augmented-assign
x = 10
x += 5; x -= 3; x *= 2; x //= 5; x **= 2; x %= 7
print(x)
#### multiple-assign-unpack
a, b, *rest = range(6)
(c, d), e = (1, 2), 3
a, b = b, a
print(a, b, rest, c, d, e)
#### big-int
print(2 ** 200 // 3 ** 50, len(str(3 ** 1000)), (10 ** 30 + 1) % 97)
#### ternary-and-lambda
f = lambda x: 'even' if x % 2 == 0 else 'odd'
print([f(i) for i in range(4)])
#### global-nonlocal
count = 0
def inc():
    global count
    count += 1
def counter():
    n = 0
    def step():
        nonlocal n
        n += 1
        return n
    return step
inc(); inc()
s = counter(); s(); s()
print(count, s())
