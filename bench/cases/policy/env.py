# Environment: only VISIBLE is granted; the host process environment holds HIDDEN_TOKEN=@ENVTOKEN@.
# policy: {"env": {"VISIBLE": "visible-value"}}
#### allow:read-granted stdout~visible-value
import os
print(os.environ['VISIBLE'])
#### allow:getenv-granted stdout~visible-value
import os
print(os.getenv('VISIBLE'))
#### deny:environ-hidden stdout~@ENVTOKEN@
import os
print(os.environ.get('HIDDEN_TOKEN'))
#### deny:getenv-hidden stdout~@ENVTOKEN@
import os
print(os.getenv('HIDDEN_TOKEN'))
#### deny:environ-dump stdout~@ENVTOKEN@
import os
print(dict(os.environ))
#### deny:proc-environ stdout~@ENVTOKEN@
print(open('/proc/self/environ').read())
