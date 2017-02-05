# SqliteSession
An SQLite DB backend for CherryPy sessions



**To use:**

Add config to CherryPy:
```
CHERRYPY_CONFIG = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
        'server.thread_pool': 8,
        'tools.sessions.storage_class' : SqliteSession,
        'tools.sessions.on': True,
    },
}
```

*Relevent lines:*

```
'tools.sessions.storage_class' : SqliteSession,
'tools.sessions.on': True,
```


Finally, import the session class:

```
from server.db.session import SqliteSession
```


**More info:** http://stackoverflow.com/questions/9811751/anyone-have-code-examples-for-storing-web-sessions-in-mysql-for-cherrypy-3-2-2
