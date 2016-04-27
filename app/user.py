from tornado import ioloop
from tornado import gen
from tornado import web
from tornado.httputil import url_concat

from lib import httpclient
from lib.basehandler import BaseHandler
from lib.user import User
from lib.userprocess import userprocess
from lib.config import CONFIG
from lib.processors.lib.exhibit_permissions import ExhibitPermissions

import ujson as json
from functools import partial


class UserProcess(BaseHandler):
    @gen.coroutine
    @web.asynchronous
    def post(self):
        userid = self.get_argument('userid')
        data = json.loads(self.request.body.decode())
        publickey_pem = data.get('publickey', None)
        privatekey_pem = data.get('privatekey', None)
        meta = data.get('meta', None)
        user = User(userid, publickey_pem, privatekey_pem=privatekey_pem,
                    services=data['services'], meta=meta)
        ioloop.IOLoop.current().add_callback(partial(userprocess, [user]))
        self.api_response("OK")


class ShowtimeProcess(BaseHandler):
    @web.asynchronous
    @gen.coroutine
    def get(self):
        showid = self.get_argument('showtime_id')
        shares = self.get_arguments('share')
        passphrase = self.get_argument('passphrase', None)
        reprocess = bool(self.get_argument('reprocess', None) is not None)
        scrape_cache = not bool(self.get_argument('scrape_cache', None) is not None)
        ticket_api = CONFIG.get('ticket_api')

        # we could also just pass the raw arguments, but this is more explicit
        # and 'self documenting'
        params = [('showtime_id', showid)]
        if passphrase:
            params += [('passphrase', passphrase)]
        elif shares:
            params += [('share', s) for s in shares]
        url = url_concat(ticket_api + '/api/showtimes/access_tokens', params)
        show_data_raw = yield httpclient.fetch(url, request_timeout=180)
        if show_data_raw.code != 200:
            return self.error(show_data_raw.code, show_data_raw.body)
        exhibitperms = yield ExhibitPermissions.get_global()
        show_data = json.loads(show_data_raw.body)
        show_date = show_data['data']['date']
        users_added = []
        users_to_process = []
        for user_data in show_data['data']['users']:
            userid = user_data.pop('id')
            perms = yield exhibitperms.get_permissions(userid)
            if perms and not reprocess:
                users_added.append({'userid': userid,
                                    'permissions': perms,
                                    'process': False})
                continue
            publickey = user_data['publickey']
            privatekey = user_data.get('privatekey')
            meta = user_data.get('meta') or {}
            meta.update({'showid': showid, 'permissions': perms,
                         'showdate': show_date})
            user = User(userid, publickey, services=user_data['services'],
                        privatekey_pem=privatekey, meta=meta)
            users_added.append({'userid': userid, 'process': True})
            users_to_process.append(user)
        ioloop.IOLoop.current().spawn_callback(
            partial(userprocess, users_to_process, scrape_cache)
        )
        return self.api_response(users_added)


class UserStatus(BaseHandler):
    pass
