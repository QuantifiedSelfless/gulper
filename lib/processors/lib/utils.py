from tornado import gen

from .exhibit_permissions import ExhibitPermissions
from ...basehandler import BaseHandler
from ...user import User


def make_handler(name, handler):
    class ProcAPIHandler(BaseHandler):
        @gen.coroutine
        def get(self):
            userid = self.get_argument('userid')
            privatekey_pem = self.get_argument('privatekey', None)
            publickey_pem = self.get_argument('publickey', None)

            exibperm = yield ExhibitPermissions.get_global()
            permission = yield exibperm.has_permission(userid, name)
            if permission is not True:
                return self.error(403, "NO_ACCESS")
            user = User(userid, publickey_pem=publickey_pem,
                        privatekey_pem=privatekey_pem)
            data = yield handler(user, self)
            return self.api_response(data)
    return ProcAPIHandler


def process_api_handler(get_handlers):
    def _(self):
        handlers = get_handlers(self)
        result = []
        for path, handler in handlers:
            handler = ("/{}/{}".format(self.name, path),
                       make_handler(self.name, handler))
            result.append(handler)
        return result
    return _
