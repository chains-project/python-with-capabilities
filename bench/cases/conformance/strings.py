#### string-methods
s = '  Hello, World  '
print(s.strip(), s.lower().strip(), s.upper(), s.strip().split(', '), s.replace('l', 'L', 2), s.count('l'))
#### string-slicing
s = 'abcdefgh'
print(s[2:5], s[::-1], s[::2], s[-3:], s[:-3], s[10:], s[1:7:3])
#### fstrings
name, n, pi = 'agent', 42, 3.14159
print(f'{name!r} {n:05d} {pi:.2f} {n:>6} {n:<6}| {n:^7}| {n:x} {n:b} {pi:e} {1234567:,} {0.25:.0%}')
#### fstring-expressions
items = {'a': 1}
print(f"{items['a'] + 1} {'nested ' + str(len(items))} {n if (n := 3) else 0} {'{'}braces{'}'}")
#### fstring-debug
x = 10
print(f'{x=} {x * 2 = }')
#### format-method-and-percent
print('{} + {} = {}'.format(1, 2, 3), '{0}{1}{0}'.format('a', 'b'), '%s is %d years, %.1f%%' % ('x', 3, 99.5))
#### string-join-split
words = 'the quick brown fox'.split()
print('-'.join(words), ','.join(map(str, range(5))), 'a,b,,c'.split(','), 'a b  c'.split(), 'x=1'.partition('='))
#### string-predicates
print('abc'.isalpha(), '123'.isdigit(), ' '.isspace(), 'Title Case'.istitle(), 'abc'.startswith(('x', 'a')), 'file.py'.endswith('.py'))
#### string-find-index
s = 'hello world'
print(s.find('o'), s.rfind('o'), s.find('z'), s.index('w'), 'o' in s)
#### unicode
s = 'héllo wörld ✓'
print(len(s), s.upper(), s.encode('utf-8')[:8], ord('é'), chr(10003), s.casefold())
#### string-padding
print('42'.zfill(5), 'ab'.center(6, '*'), 'ab'.ljust(4, '.') + '|', 'ab'.rjust(4) + '|', 'tab\there'.expandtabs(4))
#### bytes
b = b'hello'
print(b[0], b[1:3], b.decode(), bytes([65, 66]), b.hex(), bytearray(b'ab') + b'c', len(b))
#### multiline-and-raw
s = """line1
line2"""
print(s.splitlines(), r'raw\n', repr('quote\'s'), 'a' 'b')
#### str-repr
print(repr('x'), repr(1.0), repr([1, 'a', None]), str(3.0), repr({'k': (1,)}), ascii('é'))
