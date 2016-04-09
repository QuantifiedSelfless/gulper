from tornado import gen
import rethinkdb as r

from ...dbhelper import RethinkDB


_exhibit_permissions = None


@gen.coroutine
def exhibit_permissions():
    global _exhibit_permissions
    if _exhibit_permissions is None:
        _exhibit_permissions = ExhibitPermissions()
        yield _exhibit_permissions.init()
    return _exhibit_permissions


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
