from tornado import gen
import rethinkdb as r

from ...dbhelper import RethinkDB


class ExhibitPermissions(RethinkDB):
    def __init__(self):
        # gulperbase is for gulper specific data... processors should make
        # their own DB
        super().__init__('gulperbase',
                         ['exhibitpermissions'])

    @gen.coroutine
    def save_permission(self, user, processor, permission):
        conn = yield self.connection()
        yield r.table('exhibitpermissions').insert({
            'id': user,
            processor: permission,
        }, conflict='update').run(conn)

    @gen.coroutine
    def has_permission(self, user, processor):
        conn = yield self.connection()
        try:
            result = yield r.table('exhibitpermissions').get(user) \
                                .get_field(processor).run(conn)
            return result
        except:
            return False
