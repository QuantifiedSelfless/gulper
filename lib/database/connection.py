import rethinkdb as r
from tornado import gen

from ..config import CONFIG

r.set_loop_type("tornado")
_connection = None


@gen.coroutine
def connection():
    global _connection
    if _connection is None:
        _connection = yield init()
    conn = yield _connection
    return conn


@gen.coroutine
def init():
    print("starting db init")
    connection = r.connect(
        host=CONFIG.get('rethink_host'),
        port=int(CONFIG.get('rethink_port'))
    )
    print("Connecting")
    return connection
