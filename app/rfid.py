from tornado import gen
from tornado import web
from tornado.httputil import url_concat

from lib import httpclient
from lib.basehandler import BaseHandler
from lib.config import CONFIG
from lib.rfidb import RFIDB

import ujson as json


class UnlockShowtime(BaseHandler):
    @web.asynchronous
    @gen.coroutine
    def get(self):
        showid = self.get_argument('showtime_id')
        shares = self.get_arguments('share')
        passphrase = self.get_argument('passphrase', None)
        ticket_api = CONFIG.get('ticket_api')

        # we could also just pass the raw arguments, but this is more explicit
        # and 'self documenting'
        params = {'showtime_id': showid, 'shares': shares,
                  'passphrase': passphrase}
        url = url_concat(ticket_api + '/api/showtimes/access_tokens', params)
        show_data_raw = yield httpclient.fetch(url)
        if show_data_raw.code != 200:
            return self.error(show_data_raw.code, show_data_raw.body)

        show_data = json.loads(show_data_raw.body)
        show_date = show_data['data']['date']

        rfidb = RFIDB.get_global()
        result = yield rfidb.unlock_show(showid, show_date,
                                         show_data['data']['users'])
        return self.api_response(result)


class ListShowtimeUsers(BaseHandler):
    @web.asynchronous
    @gen.coroutine
    def get(self):
        rfidb = RFIDB.get_global()
        users = yield rfidb.list_users()
        return self.api_response(users)
