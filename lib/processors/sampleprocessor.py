from tornado import gen
from .utils import process_api_handler


class SampleProcessor(object):
    name = 'sample_processor'
    data = {}

    @gen.coroutine
    def process(self, user_data):
        print("Processing user: ", user_data.userid)
        userid = user_data.userid
        self.data[userid] = sum(len(i['text']) for i in user_data.data['text'])
        print("Result: ", self.data[userid])
        return True

    @gen.coroutine
    def num_characters(self, userid, request, public_key=None):
        return self.data.get(userid, 'userid not found')

    @process_api_handler
    def register_handlers(self):
        return [
            ('num_characters', self.num_characters),
        ]

