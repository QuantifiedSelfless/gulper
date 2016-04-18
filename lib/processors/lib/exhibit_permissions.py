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
    def save_permission(self, user, name, processor, permission):
        conn = yield self.connection()
        yield r.table('exhibitpermissions').insert({
            'id': user,
            'name': name,
            processor: permission,
        }, conflict='update').run(conn)

    @gen.coroutine
    def has_permission(self, user, processor):
        conn = yield self.connection()
        try:
            result = yield r.table('exhibitpermissions').get(user) \
                                .pluck(processor).run(conn)
            return result
        except:
            return False

    @gen.coroutine
    def permission_meta(self, user, processor):
        conn = yield self.connection()
        try:
            result = yield r.table('exhibitpermissions').get(user) \
                                .pluck('name', processor).run(conn)
            return {"permission": result[processor],
                    "name": result['name']}
        except:
            return {"permission": False, "name": None}
