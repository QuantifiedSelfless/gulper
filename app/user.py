from tornado import gen
from tornado import web
from lib.basehandler import BaseHandler

import json


class UserProcess(BaseHandler):
    @gen.coroutine
    @web.asynchronous
    def post(self):
        userid = self.get_argument('userid')
        publickey = self.get_argument('publickey')
        data = json.loads(self.request.body)
        # create user object and trigger scrape/process


class UserStatus(BaseHandler):
    pass
