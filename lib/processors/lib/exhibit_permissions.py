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
    def save_permission(self, user_data, processor, permission):
        conn = yield self.connection()
        yield r.table('exhibitpermissions').insert({
            'id': user_data.userid,
            'name': user_data.meta.get('name'),
            processor: permission,
        }, conflict='update').run(conn)

    @gen.coroutine
    def delete_permissions(self, user_data):
        conn = yield self.connection()
        result = yield r.table('exhibitpermissions').get(user_data.userid) \
                        .delete().run(conn)
        return bool(result.get('deleted'))

    @gen.coroutine
    def get_permissions(self, user):
        conn = yield self.connection()
        try:
            result = yield r.table('exhibitpermissions').get(user).run(conn)
            return result
        except:
            return {}

    @gen.coroutine
    def has_permission(self, user, processor):
        conn = yield self.connection()
        try:
            result = yield r.table('exhibitpermissions').get(user) \
                            .get_field(processor).run(conn)
            return result
        except:
            return False

    @gen.coroutine
    def has_permission_meta(self, user, processor):
        conn = yield self.connection()
        try:
            result = yield r.table('exhibitpermissions').get(user) \
                                .pluck('name', processor).run(conn)
            return {"permission": result[processor],
                    "name": result['name']}
        except:
            return {"permission": False, "name": None}
