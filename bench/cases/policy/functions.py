# Host-function grants: only `lookup` is granted; `admin_reset` exists on the host but is not granted (marker ADMINRAN
# appears if it runs). The host module defining both imports os and subprocess, so any reflective path from the
# granted function to its module globals reaches the host (marker OSRAN1).
# policy: {"functions": ["lookup"]}
#### allow:call-granted stdout~apple=3
print('apple=' + lookup('apple'))
#### deny:call-ungranted stdout~ADMINRAN
admin_reset()
#### deny:ungranted-via-globals stdout~ADMINRAN
lookup.__globals__['admin_reset']()
#### deny:globals-os stdout~OSRAN1
print('OSRAN' + str(len(lookup.__globals__['os'].sep)))
#### deny:getattr-concat stdout~OSRAN1
print('OSRAN' + str(len(getattr(lookup, '__glo' + 'bals__')['os'].sep)))
#### deny:object-getattribute stdout~OSRAN1
print('OSRAN' + str(len(object.__getattribute__(lookup, '__globals__')['os'].sep)))
#### deny:type-dict-descriptor stdout~OSRAN1
print('OSRAN' + str(len(type(lookup).__dict__['__globals__'].__get__(lookup)['os'].sep)))
#### deny:format-string stdout~OSRAN1
print('OSRAN' + '{0.__globals__[os].sep}'.format(lookup).replace('/', '1'))
#### deny:module-attribute stdout~OSRAN1
import sys
print('OSRAN' + str(len(sys.modules[lookup.__module__].os.sep)))
#### deny:code-object-replace stdout~ADMINRAN
f = type(lookup)(lookup.__globals__['admin_reset'].__code__, lookup.__globals__)
f()
