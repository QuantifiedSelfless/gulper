from tornado import gen

from .lib.handler import process_api_handler
from .lib.baseprocessor import BaseProcessor

import random


class OwnupProcessor(BaseProcessor):
    name = 'ownup'
    limit = 10

    def __init__(self):
        super().__init__()
        self.keywords = self.load_keywords('ownup.txt')

    def is_great_quote(self, text):
        text = text.lower()
        for word in self.keywords:
            if text.find(word) >= 0:
                return True
        return False

    """ Return True if processing should continue
    """
    def process_post(self, text, temp, perm):
        # If there is enough perm quotes, quit.
        if len(perm) >= self.limit:
            return False
        sentences = text.split('.')
        for sentence in sentences:
            if self.is_great_quote(sentence):
                perm.append(sentence)
                random.shuffle(perm)
            elif len(sentence) > 15:
                temp.append(sentence)
                random.shuffle(perm)
        return True

    def process_facebook(self, user_data, temp, perm):
        if user_data.data.get('fbtext', None):
            fbtext = user_data.data.get('fbtext')
            if not fbtext or len(perm) >= self.limit:
                return
            fbposts = fbtext['text']
            for post in fbposts:
                if not self.process_post(post['text'], temp, perm):
                    return

    def process_twitter(self, user_data, temp, perm):
        if user_data.data.get('twitter', None):
            twitter = user_data.data.get('twitter', None)
            if not twitter or len(perm) >= self.limit:
                return
            tweets = twitter['tweets']
            for post in tweets:
                if not self.process_post(post, temp, perm):
                    return

    def process_reddit(self, user_data, temp, perm):
        if user_data.data.get('reddit', None):
            reddit = user_data.data.get('reddit', None)
            if not reddit or len(perm) >= self.limit:
                return
            posts = reddit['text']
            for post in posts:
                if not self.process_post(post['body'], temp, perm):
                    return

    @gen.coroutine
    def process(self, user_data):
        self.logger.info("[OU] Processing user: {}".format(user_data.userid))
        temp = []
        perm = []
        self.process_facebook(user_data, temp, perm)
        self.process_twitter(user_data, temp, perm)
        self.process_reddit(user_data, temp, perm)
        while len(perm) < self.limit and len(temp) > 1:
            perm.append(temp.pop())
        if len(perm) < 3:
            return False
        blob = {'name': user_data.meta['name'], 'quotes': perm}
        self.save_user_blob(blob, user_data)
        return True

    @gen.coroutine
    def get_quotes(self, user, request):
        return self.load_user_blob(user)

    @process_api_handler
    def register_handlers(self):
        return [
            ('quotes', self.get_quotes),
        ]
