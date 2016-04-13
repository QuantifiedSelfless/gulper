from tornado import gen

from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


class MentalHealthProcessor(BaseProcessor):
    name = 'mental_health'
    limit = 200

    def __init__(self):
        super().__init__()
        try:
            fd = open('./lib/processors/lib/mentalwords.txt', 'r')
            raw = fd.read()
            fd.close()
            self.keywords = raw.split('\n')
            self.logger.info("Loaded stop words for analysis")
        except (IOError, ValueError):
            self.logger.info("Stop words not availble")

    def is_good_quote(self, text):
        text = text.lower()
        for word in self.keywords:
            if text.find(word) > 0:
                return True
        return False

    """ Return True if processing should continue
    """
    def process_post(self, text, quotes):
        if len(quotes) >= self.limit:
            return False
        if self.is_good_quote(text):
            quotes.append(text)
        return True

    def process_facebook(self, user_data, quotes):
        if user_data.data.get('fbtext', None):
            fbtext = user_data.data.get('fbtext')
            if not fbtext or len(quotes) >= self.limit:
                return
            fbposts = fbtext.get('text', None)
            for post in fbposts:
                if not self.process_post(post['text'], quotes):
                    return

    def process_twitter(self, user_data, quotes):
        if user_data.data.get('twitter', None):
            twitter = user_data.data.get('twitter')
            if not twitter or len(quotes) >= self.limit:
                return
            tweets = twitter.get('tweets', None)
            for post in tweets:
                if not self.process_post(post, quotes):
                    return

    def process_reddit(self, user_data, quotes):
        if user_data.data.get('reddit', None):
            reddit = user_data.data.get('reddit')
            if not reddit or len(quotes) >= self.limit:
                return
            print(reddit.keys())
            posts = reddit.get('text', None)
            for post in posts:
                if not self.process_post(post['body'], quotes):
                    return

    def process_gtext(self, user_data, quotes):
        if user_data.data.get('gtext', None):
            gtext = user_data.data.get('gtext', None)
            if not gtext or len(quotes) >= self.limit:
                return
            posts = gtext['snippets']
            for post in posts:
                if not self.process_post(post, quotes):
                    return

    @gen.coroutine
    def process(self, user_data):
        self.logger.info("[MH] Processing user: {}".format(user_data.userid))
        quotes = []
        self.process_facebook(user_data, quotes)
        self.process_twitter(user_data, quotes)
        self.process_reddit(user_data, quotes)
        self.process_gtext(user_data, quotes)
#        print(quotes)
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
