from tornado import ioloop
from tornado import gen
from tornado import web
from tornado.httputil import url_concat
from tornado.httpclient import AsyncHTTPClient

from lib.basehandler import BaseHandler
from lib.userscraper import UserScraper
from lib.config import CONFIG

import ujson as json


class UserProcess(BaseHandler):
    @gen.coroutine
    @web.asynchronous
    def post(self):
        userid = self.get_argument('userid')
        publickey = self.get_argument('publickey', None)
        data = json.loads(self.request.body.decode())
        user = UserScraper(userid, publickey, data)
        ioloop.IOLoop.current().add_callback(user.start)
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
            user = UserScraper(userid, publickey, user_data['services'],
                               privatekey_pem=privatekey)
            users_added.append(userid)
            ioloop.IOLoop.current().add_callback(user.start)
        return self.api_response(users_added)


class UserStatus(BaseHandler):
    pass
