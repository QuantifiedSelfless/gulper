from tornado import gen

from ...basehandler import BaseHandler
from ...user import User
from ...database.db import get_user


def make_handler(handler):
    class ProcAPIHandler(BaseHandler):
        @gen.coroutine
        def get(self):
            userid = self.get_argument('userid')
            privatekey_pem = self.get_argument('privatekey', None)
            publickey_pem = self.get_argument('publickey', None)
            user_blob = get_user(userid)
            user_name = user_blob['name']
            user = User(userid, user_name,
                        publickey_pem=publickey_pem,
                        privatekey_pem=privatekey_pem)
            data = yield handler(user, self)
            return self.api_response(data)
    return ProcAPIHandler


def process_api_handler(get_handlers):
    def _(self):
        handlers = get_handlers(self)
        result = []
        for path, handler in handlers:
            handler = ("/{}/{}".format(self.name, path), make_handler(handler))
            result.append(handler)
        return result
    return _
