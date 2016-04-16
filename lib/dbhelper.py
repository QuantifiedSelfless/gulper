from tornado import gen
import rethinkdb as r
import logging

from .config import CONFIG


r.set_loop_type("tornado")
FORMAT = '[%(levelname)1.1s %(asctime)s %(name)s:%(lineno)d] %(message)s'
object_cache = {}


class RethinkDB(object):
    def __init__(self, dbname, tables, secondary_indicies=None):
        self._connection = None
        self.secondary_indicies = secondary_indicies or {}
        self.dbname = dbname
        self.tables = tables
        logging.basicConfig(format=FORMAT)
        self.logger = logging.getLogger("rethinkdb." + dbname)

    @classmethod
    @gen.coroutine
    def get_global(cls):
        global object_cache
        db = object_cache.get(cls)
        if db is None:
            object_cache[cls] = True
            db = cls()
            yield db.init()
            object_cache[cls] = db
        elif db is True:
            while db is True:
                yield gen.sleep(0)
                db = object_cache.get(cls)
        return db

    @gen.coroutine
    def connection(self):
        # loop makes sure that the connection object has been completely
        # initialized before we use it (note that we only set the
        # self._connection object at the END of self.init()
        while self._connection is None:
            yield gen.sleep(0)
        conn = yield self._connection
        return conn

    @gen.coroutine
    def init(self):
        self.logger.info("Initializing connection to DB")
        connection = r.connect(
            host=CONFIG.get('rethink_host'),
            port=int(CONFIG.get('rethink_port')),
            db=self.dbname
        )
        conn = yield connection
        try:
            yield r.db_create(self.dbname).run(conn)
        except r.ReqlRuntimeError:
            self.logger.debug("Database already exists")
        finally:
            conn.use(self.dbname)

        for table in self.tables:
            try:
                yield r.table_create(table).run(conn)
            except r.ReqlOpFailedError:
                self.logger.debug("Table already exists: " + table)
            if table in self.secondary_indicies:
                idxs = self.secondary_indicies[table]
                for idx in idxs:
                    try:
                        yield r.table(table).index_create(**idx)
                    except r.ReqlRuntimeError:
                        self.logger.debug("Table index exists: "
                                          "{}: {}".format(table, idx))

        yield r.db(self.dbname).wait().run(conn)
        self.logger.info("Done initializing DB")
        self._connection = connection
        return connection
