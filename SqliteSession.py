"""
SQLite DB backend for CherryPy sessions.
http://stackoverflow.com/questions/9811751/anyone-have-code-examples-for-storing-web-sessions-in-mysql-for-cherrypy-3-2-2
"""

import hashlib
import sqlite3
import datetime
import cherrypy
import threading

import server.db as db

try:
  import cPickle as pickle
except ImportError:
  import pickle

from cherrypy.lib.sessions import Session


class SqliteSession(Session):
    locks = {}

    @classmethod
    def setup(cls, **kwargs):
        """Set up the storage system for redis-based sessions.
        Called once when the built-in tool calls sessions.init.
        """
        # overwritting default settings with the config dictionary values
        for k, v in kwargs.items():
            setattr(cls, k, v)

        cls.db = db.DB(cherrypy).init()
        cls.pickle_protocol = 0

    def _exists(self):
        # Select session data from table
        sql = 'select data, expiration_time from session where id = ?'
        return bool(self.db.execSQL(db.DB_CMD_TYPE.SQL, [(sql, (self.id,))]))

    def _load(self):
        # Select session data from table
        sql = '''select data, expiration_time "expiration_time [timestamp]" from session where id = ?'''
        rows = self.db.execSQL(db.DB_CMD_TYPE.SQL, [(sql, (self.id,))])
        if not rows:
            return None

        pickled_data = rows[0]['data']
        expiration_time = rows[0]['expiration_time']
        #http://stackoverflow.com/questions/7588511/format-a-datetime-into-a-string-with-milliseconds
        dt = datetime.datetime.strptime(expiration_time, '%Y-%m-%d %H:%M:%S.%f')
        data = pickle.loads(pickled_data.encode('utf-8'))
        return (data, dt)

    def _save(self, expiration_time):
        pickled_data = pickle.dumps(self._data)
        #http://stackoverflow.com/questions/15277373/sqlite-upsert-update-or-insert
        sql1 = 'INSERT OR IGNORE INTO session (id, data, expiration_time) VALUES (?, ?, ?);'
        self.db.execSQL(db.DB_CMD_TYPE.SQL, [(sql1, (self.id, pickled_data, expiration_time,))])
        sql2 = 'UPDATE session SET id = ?, data = ?, expiration_time = ? WHERE id = ?;'
        self.db.execSQL(db.DB_CMD_TYPE.SQL, [(sql2, (self.id, pickled_data, expiration_time, self.id,))])

    def _delete(self):
        print '------------ DELETING ---------------'
        sql = 'delete from session where id = ?'
        self.db.execSQL(db.DB_CMD_TYPE.SQL, [(sql, (self.id,))])

    # http://docs.cherrypy.org/dev/refman/lib/sessions.html?highlight=session#locking-sessions
    # session id locks as done in RamSession

    def acquire_lock(self):
        """Acquire an exclusive lock on the currently-loaded session data."""
        self.locked = True
        self.locks.setdefault(self.id, threading.RLock()).acquire()
        cherrypy.log('Lock acquired.', 'TOOLS.SESSIONS')

    def release_lock(self):
        """Release the lock on the currently-loaded session data."""
        self.locks[self.id].release()
        self.locked = False

    def clean_up(self):
        """Clean up expired sessions."""
        sql = 'delete from session where expiration_time < ?'
        self.db.execSQL(db.DB_CMD_TYPE.SQL, [(sql, (datetime.datetime.now(),))])
