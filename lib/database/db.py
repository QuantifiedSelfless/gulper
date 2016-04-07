from tornado import gen
import rethinkdb as r

from .connection import connection


@gen.coroutine
def get_user(uid):
    conn = yield connection()
    result = yield r.table('users').get(uid).run(conn)
    return result
