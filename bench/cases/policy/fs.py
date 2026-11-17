# Path grants: src/ read-only, out/ read-write, nothing else (words.txt and secrets/ are not granted).
# secrets/key.txt holds a per-run token (@TOKEN@). host+P / host-P / hostchg P: P created / removed / changed.
# policy: {"fs": {"src": "ro", "out": "rw"}}
#### allow:read-src stdout~from lib.helper
print(open('src/main.py').read())
#### allow:write-out host+out/a.txt
open('out/a.txt', 'w').write('hi')
#### allow:copy-src-to-out host+out/u.py
open('out/u.py', 'w').write(open('src/util.py').read())
#### deny:read-secret stdout~@TOKEN@
print(open('secrets/key.txt').read())
#### deny:read-secret-src-dotdot stdout~@TOKEN@
print(open('src/../secrets/key.txt').read())
#### deny:read-secret-out-dotdot stdout~@TOKEN@
print(open('out/../secrets/key.txt').read())
#### deny:read-secret-pathlib-glob stdout~@TOKEN@
from pathlib import Path
print([p.read_text() for p in Path('.').glob('secr*/*')])
#### deny:read-secret-host-abs-path stdout~@TOKEN@
print(open('@WORK@/secrets/key.txt').read())
#### deny:read-ungranted-file stdout~elderberry
print(open('words.txt').read())
#### deny:read-outside-abs stdout~@TOKEN@
print(open('@SECRET@').read())
#### deny:write-src host+src/new.txt
open('src/new.txt', 'w').write('x')
#### deny:append-src hostchg src/main.py
open('src/main.py', 'a').write('x')
#### deny:remove-src host-src/util.py
from pathlib import Path
Path('src/util.py').unlink()
#### deny:rename-src-to-out host-src/util.py
from pathlib import Path
Path('src/util.py').rename('out/util.py')
#### deny:write-ungranted-root host+new.txt
open('new.txt', 'w').write('x')
#### deny:write-out-dotdot host+escaped.txt
open('out/../escaped.txt', 'w').write('x')
#### deny:mkdir-ungranted host+newdir
from pathlib import Path
Path('newdir').mkdir()
#### deny:overwrite-secret hostchg secrets/key.txt
open('secrets/key.txt', 'w').write('x')
#### deny:symlink-in-out stdout~@TOKEN@
import os
os.symlink('../secrets', 'out/s')
print(open('out/s/key.txt').read())
