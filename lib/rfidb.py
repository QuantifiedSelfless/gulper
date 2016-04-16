from tornado import gen
import rethinkdb as r

from .dbhelper import RethinkDB
from .user import User


class RFIDB(RethinkDB):
    def __init__(self):
        # gulperbase is for gulper specific data... processors should make
        # their own DB
        super().__init__('gulperbase', ['rfid'],
                         secondary_indicies={'rfid': ['rfid', 'showid']})

    @gen.coroutine
    def unlock_show(self, showid, date, users):
        conn = yield self.connection()
        objects = []
        for user in users:
            print(user)
            objects.append({
                'id': user['id'],
                'publickey': user['publickey'],
                'privatekey': user['privatekey'],
                'name': user['meta']['name'],
                'email': user['meta']['email'],
                'showid': user['meta']['showid'],
                'showdate': date,
                'rfid': None,
            })
        yield r.table('rfid').insert(*objects, conflict='update').run(conn)

    @gen.coroutine
    def list_users(self):
        conn = yield self.connection()
        try:
            result = yield r.table('rfid').without('privatekey', 'publickey') \
                            .run(conn)
            return result
        except:
            return []

    @gen.coroutine
    def associate_user(self, userid, rfid):
        conn = yield self.connection()
        try:
            result = yield r.table('rfid').get(userid).update({'rfid': rfid}) \
                            .run(conn)
            return result
        except:
            self.logger.exception("Unable to associate user: "
                                  "{} <-> {}".format(userid, rfid))
            return False

    @gen.coroutine
    def rfid_to_user(self, rfid):
        conn = yield self.connection()
        try:
            userdata = yield r.table('rfid').get_all(rfid, index='rfid') \
                            .sort(r.desc('showdate')).limit(1).run(conn)
            return self.userdata_to_obj(userdata)
        except:
            self.logger.exception("Unable to get user for "
                                  "rfid: {}".format(rfid))
            return None

    @staticmethod
    def userdata_to_obj(userdata):
        userid = userdata.pop('id')
        privatekey_pem = userdata.pop('privatekey')
        publickey_pem = userdata.pop('publickey')
        return User(userid, publickey_pem=publickey_pem,
                    privatekey_pem=privatekey_pem, meta=userdata)
