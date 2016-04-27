from tornado import gen

import random

from .lib.handler import process_api_handler
from .lib.baseprocessor import BaseProcessor
from .lib import keyword_filters


class MentalHealthProcessor(BaseProcessor):
    name = 'mental_health'
    num_quotes = 200

    def __init__(self):
        super().__init__()
        self.keywords = self.load_keywords('mentalwords.txt')

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
        quotes += list(keyword_filters.process_gmail(user_data,
                                                     self.keywords))
        self.logger.debug("User {}: {} quotes".format(user_data.userid,
                                                      len(quotes)))
        if len(quotes) < 5:
            return False
        if len(quotes) > self.num_quotes:
            quotes = random.sample(quotes, self.num_quotes)
        self.save_user_blob(quotes, user_data)
        return True

    @gen.coroutine
    def get_quotes(self, user, request):
        return self.load_user_blob(user)

    @process_api_handler
    def register_handlers(self):
        return [
            ('quotes', self.get_quotes),
        ]
