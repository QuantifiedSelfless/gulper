from tornado import gen
from .utils import process_api_handler


class SampleProcessor(object):
    name = 'sample_processor'
    data = {}

    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares
        """
        print("Processing user: ", user_data.userid)
        userid = user_data.userid
        #self.data[userid] = sum(
         #   len(i['text'])
          #  for i in user_data.data['samplescraper']
        #)
        #print("Result: ", self.data[userid])
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
