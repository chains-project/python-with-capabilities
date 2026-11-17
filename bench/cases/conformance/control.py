#### if-elif-else
for n in [1, 5, 10]:
    if n < 3:
        print('small')
    elif n < 8:
        print('mid')
    else:
        print('big')
#### while-else-break
n = 0
while n < 10:
    n += 3
    if n == 9:
        break
else:
    print('no break')
print(n)
#### for-else
for i in range(3):
    pass
else:
    print('loop done', i)
#### match-statement
def kind(v):
    match v:
        case 0:
            return 'zero'
        case int(x) if x < 0:
            return 'negative'
        case [a, b]:
            return f'pair {a},{b}'
        case {'type': t}:
            return f'typed {t}'
        case str() | bytes():
            return 'text'
        case _:
            return 'other'
print([kind(v) for v in [0, -3, [1, 2], {'type': 'x'}, 'hi', 3.5]])
#### nested-loops-continue
for i in range(3):
    for j in range(3):
        if j == i:
            continue
        print(i, j, end='; ')
print()
#### print-options
print('a', 'b', sep='-', end='!\n')
print(*[1, 2, 3])
print()
