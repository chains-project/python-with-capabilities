# Resource-exhaustion probes. "contained" = the runtime ends the run on its own before the harness deadline, with
# peak RSS and output under the harness caps. Runs inside a systemd scope with MemoryMax and TasksMax so that
# CPython (the known-positive control) cannot hurt the host.
#### infinite-loop
while True:
    pass
#### infinite-recursion-caught
def f():
    try:
        f()
    except RecursionError:
        f()
f()
#### memory-string-doubling
x = 'a'
while True:
    x = x + x
#### memory-list-growth
xs = []
while True:
    xs.append([0] * 1000)
#### big-int-power
print(len(str(7 ** (10 ** 9))))
#### output-flood
while True:
    print('y' * 1000)
#### regex-backtracking
import re
print(re.match(r'(a+)+$', 'a' * 64 + 'b'))
#### sleep-forever
import time
time.sleep(100000)
#### swallow-everything
while True:
    try:
        while True:
            pass
    except BaseException:
        pass
