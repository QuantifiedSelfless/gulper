from tornado import ioloop
from tornado import gen
from tornado import web
from tornado.httputil import url_concat
from tornado.httpclient import AsyncHTTPClient

from lib.basehandler import BaseHandler
from lib.user import User
from lib.userprocess import userprocess
from lib.config import CONFIG

import ujson as json
from functools import partial


class UserProcess(BaseHandler):
    @gen.coroutine
    @web.asynchronous
    def post(self):
        userid = self.get_argument('userid')
        publickey = self.get_argument('publickey', None)
        data = json.loads(self.request.body.decode())
        user = User(userid, publickey, services=data)
        ioloop.IOLoop.current().add_callback(partial(userprocess, user))
        self.api_response("OK")


class ShowtimeProcess(BaseHandler):
    @web.asynchronous
    @gen.coroutine
    def get(self):
        showid = self.get_argument('showtime_id')
        shares = self.get_arguments('share')
        passphrase = self.get_argument('passphrase', None)
        http_client = AsyncHTTPClient()
        ticket_api = CONFIG.get('ticket_api')

        # we could also just pass the raw arguments, but this is more explicit
        # and 'self documenting'
        params = {'showtime_id': showid, 'shares': shares,
                  'passphrase': passphrase}
        url = url_concat(ticket_api + '/api/showtimes/access_tokens', params)
        show_data_raw = yield http_client.fetch(url)
        if show_data_raw.code != 200:
            return self.error(show_data_raw.code, show_data_raw.body)
        show_data = json.loads(show_data_raw.body)
        users_added = []
        for user_data in show_data['data']['users']:
            userid = user_data.pop('id')
            publickey = user_data['publickey']
            privatekey = user_data['privatekey']
            user = User(userid, publickey, services=user_data['services'],
                        privatekey_pem=privatekey)
            users_added.append(userid)
            ioloop.IOLoop.current().add_callback(partial(userprocess, user))
        return self.api_response(users_added)


class UserStatus(BaseHandler):
    pass
