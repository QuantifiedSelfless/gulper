from tornado import gen

from .lib.handler import process_api_handler
from .lib.baseprocessor import BaseProcessor
from .lib import keyword_filters

import random


class OwnupProcessor(BaseProcessor):
    name = 'ownup'
    num_quotes = 100

    def __init__(self):
        super().__init__()
        self.keywords = self.load_keywords('ownup.txt')

    @gen.coroutine
    def process(self, user_data):
        self.logger.info("Processing user: {}".format(user_data.userid))
        quotes = []
        quotes += list(keyword_filters.process_facebook(user_data,
                                                        self.keywords))
        quotes += list(keyword_filters.process_twitter(user_data,
                                                       self.keywords))
        quotes += list(keyword_filters.process_reddit(user_data,
                                                      self.keywords))
        self.logger.debug("User %s has %d quotes", user_data.userid, len(quotes))
        if not quotes:
            return False
        if len(quotes) > self.num_quotes:
            quotes = random.sample(quotes, self.num_quotes)
        blob = {'name': user_data.meta['name'],
                'quotes': quotes}
        self.save_user_blob(blob, user_data)
        return True

    @gen.coroutine
    def get_quotes(self, user, request):
        data = self.load_user_blob(user)
        if len(data['quotes']) > 10:
            data['quotes'] = random.sample(data['quotes'], 10)
        return data

    @process_api_handler
    def register_handlers(self):
        return [
            ('quotes', self.get_quotes),
        ]
