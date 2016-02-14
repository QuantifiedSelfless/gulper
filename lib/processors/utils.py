from tornado import gen
import cryptohelper

from ..basehandler import BaseHandler


def make_handler(handler):
    class ProcAPIHandler(BaseHandler):
        @gen.coroutine
        def get(self):
            userid = self.get_argument('userid')
            privatekey_pem = self.get_argument('privatekey', None)
            privatekey = None
            if privatekey_pem:
                privatekey = cryptohelper.import_key(privatekey)
            data = yield handler(userid, privatekey)
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
