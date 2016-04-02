from tornado import gen

from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


class SampleProcessor(BaseProcessor):
    name = 'sample_processor'
    data = {}

    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares
        """
        self.logger.info("Processing user: {}".format(user_data.userid))
        userid = user_data.userid
        if not user_data.data.get('samplescraper'):
            return False
        self.data[userid] = sum(
            len(i['text'])
            for i in user_data.data['samplescraper']
        )
        return True

    @gen.coroutine
    def num_characters(self, userid, request, private_key=None):
        """
        Returns relevant data that the exhibits may want to know
        """
        return self.data.get(userid, 'userid not found')

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('num_characters', self.num_characters),
        ]
