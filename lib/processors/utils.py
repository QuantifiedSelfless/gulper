from tornado import gen
import cryptohelper

from ..basehandler import BaseHandler


def process_api_handler(handler):
    class ProcAPIHandler(BaseHandler):
        h = gen.coroutine(handler)
        def get(self):
            userid = self.get_argument('userid')
            privatekey_pem = self.get_argument('privatekey', None)
            privatekey = None
            if privatekey_pem:
                privatekey = cryptohelper.import_key(privatekey)
            data = yield self.h(userid, privatekey)
            return self.api_response(data)
    return ProcAPIHandler
