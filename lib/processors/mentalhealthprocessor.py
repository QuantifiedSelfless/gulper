from tornado import gen
import itertools as IT

from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


class MentalHealthProcessor(BaseProcessor):
    name = 'mental_health'
    limit = 200

    def __init__(self):
        super().__init__()
        self.keywords = self.load_keywords('mentalwords.txt')

    def is_good_quote(self, text):
        text = text.lower()
        for word in self.keywords:
            if word in text:
                return True
        return False

    def process_facebook(self, user_data):
        if user_data.data.get('fbtext'):
            fbtext = user_data.data['fbtext']
            fbposts = fbtext.get('text', [])
            for post in fbposts:
                yield post['text']

    def process_twitter(self, user_data):
        if user_data.data.get('twitter'):
            twitter = user_data.data['twitter']
            tweets = twitter.get('tweets', [])
            for post in tweets:
                yield post

    def process_reddit(self, user_data):
        if user_data.data.get('reddit'):
            reddit = user_data.data['reddit']
            posts = reddit.get('text', [])
            for post in posts:
                yield post['body']

    def process_gmail(self, user_data):
        if user_data.data.get('gmail'):
            gmail = user_data.data['gmail']
            for post in gmail.get('snippet', []):
                yield post

    @gen.coroutine
    def process(self, user_data):
        self.logger.info("Processing user: {}".format(user_data.userid))
        quote_candidates = IT.chain(self.process_facebook(user_data),
                                    self.process_twitter(user_data),
                                    self.process_reddit(user_data),
                                    self.process_gmail(user_data))
        quotes = list(IT.islice(quote_candidates, self.limit))
        self.logger.debug("User {}: {} quotes".format(user_data.userid,
                                                      len(quotes)))
        if len(quotes) < 0:
            return False
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
