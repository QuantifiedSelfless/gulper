from tornado import gen
from .lib.utils import process_api_handler

import random
from .lib.baseprocessor import BaseProcessor


class NewsProcessor(BaseProcessor):
    name = 'news_processor'

    def __init__(self):
        super().__init__()

    def fb_proxy(self, prof):
        parties = ['liberal', 'dem', 'moderate', 'cent', 'repub', 'conserv']
        if 'political' in prof:
            for i, party in enumerate(parties):
                if party in prof['political'].lower():
                    return i
        return None

    def reddit_proxy(self, prof):
        subs1 = ['hacking', 'crypto', 'politics', 'trees', 'apple', 'the_donald']
        if 'subs' in prof:
            for sub in prof['subs']:
                for i, subr in enumerate(subs1):
                    if subr in sub['name'].lower():
                        return i
        return None

    def like_lookup(self, likes):
        interests1 = ['snowden', 'data', 'hack', 'books', 'apple', 'nsa']
        for like in likes:
            for i, inter in enumerate(interests1):
                if inter in like.lower():
                    return i
        return None

    def follow_lookup(self, twit):
        if twit.get('following'):
            interests1 = ['snowden', 'data', 'hack', 'books', 'apple', 'nsa']
            for follow in twit['following']:
                for i, inter in enumerate(interests1):
                    if inter in follow['name'].lower():
                        return i
        return None

    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares..haha
        """
        data = {}
        data['category'] = None
        if user_data.data.get('fbprofile'):
            data['category'] = self.fb_proxy(user_data.data['fbprofile'])
        if data['category'] is None:
            if user_data.data.get('reddit'):
                data['category'] = self.reddit_proxy(user_data.data['reddit'])
        if data['category'] is None:
            if user_data.data.get('fblikes'):
                data['category'] = self.like_lookup(user_data.data['fblikes'])
        if data['category'] is None:
            if user_data.data.get('twitter'):
                data['category'] = self.follow_lookup(user_data.data['twitter'])
        if data['category'] is None:
            data['category'] = random.randint(0, 5)

        self.save_user_blob(data, user_data)
        return True

    @gen.coroutine
    def get_category(self, user, request):
        """
        Returns relevant data that the exhibits may want to know
        """
        data = self.load_user_blob(user)
        return data

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('news_category', self.get_category),
        ]
