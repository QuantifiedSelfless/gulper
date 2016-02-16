from tornado import ioloop
from tornado import gen
from tornado import web

from lib.basehandler import BaseHandler
from lib.userscraper import UserScraper

import json


class UserProcess(BaseHandler):
    @gen.coroutine
    @web.asynchronous
    def post(self):
        userid = self.get_argument('userid')
        publickey = self.get_argument('publickey', None)
        data = json.loads(self.request.body.decode())

        enable_processing = self.application.settings['enable_processing']
        # TODO: create user object and trigger scrape/process
        if enable_processing:
            user = UserScraper(userid, publickey, data)
            ioloop.IOLoop.current().add_callback(user.start)
        self.api_response("OK")


class UserStatus(BaseHandler):
    pass
