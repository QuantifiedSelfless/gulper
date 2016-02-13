from tornado import gen
from utils import process_api_handler


class SampleProcessor(object):
    data = {}

    @gen.coroutine
    def process(self, user_data):
        userid = user_data.userid
        self.data[userid] = sum(len(i['text']) for i in user_data['text'])
        return True

    def register_handlers(self):
        return [
            ('/num_characters', self.num_characters),
        ]

    @process_api_handler
    def num_characters(self, userid, public_key=None):
        return self.data.get(userid, 'userid not found')
