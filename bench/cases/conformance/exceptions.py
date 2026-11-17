#### try-except-else-finally
def div(a, b):
    try:
        r = a / b
    except ZeroDivisionError as e:
        print('error:', e)
        return None
    else:
        print('ok')
        return r
    finally:
        print('finally')
print(div(1, 2), div(1, 0))
#### custom-exception
class AppError(Exception):
    def __init__(self, code):
        super().__init__(f'code {code}')
        self.code = code
try:
    raise AppError(42)
except AppError as e:
    print(type(e).__name__, e, e.code)
#### exception-chaining
try:
    try:
        int('x')
    except ValueError as e:
        raise KeyError('wrapped') from e
except KeyError as e:
    print(repr(e), type(e.__cause__).__name__)
#### multiple-except
for v in ['1', 'x', None]:
    try:
        print(int(v))
    except (ValueError, TypeError) as e:
        print(type(e).__name__)
#### uncaught-exception-exit-code
print('before')
raise RuntimeError('boom')
#### assert
try:
    assert 1 == 2, 'math broke'
except AssertionError as e:
    print('assert:', e)
#### exception-groups
try:
    raise ExceptionGroup('many', [ValueError('a'), TypeError('b')])
except* ValueError as eg:
    print('values', [str(e) for e in eg.exceptions])
except* TypeError as eg:
    print('types', [str(e) for e in eg.exceptions])
#### builtin-error-messages
for f in [lambda: [][1], lambda: {}['k'], lambda: None.x, lambda: 1 + 'a']:
    try:
        f()
    except Exception as e:
        print(type(e).__name__, e)
#### sys-exit-code
import sys
print('exiting')
sys.exit(3)
