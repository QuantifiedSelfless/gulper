from tornado import gen
from .lib.utils import process_api_handler

import re
import random
from .lib.baseprocessor import BaseProcessor


class NewsProcessor(BaseProcessor):
    name = 'news_processor'

    def __init__(self):
        super().__init__()

    def fb_proxy(self, prof):
        if 'political' in prof:
            dem = re.search('dem', prof['political'].lower())
            liberal = re.search('liberal', prof['political'].lower())
            repub = re.search('repub', prof['political'].lower())
            cons = re.search('conservative', prof['political'].lower())
            mod = re.search('moderate', prof['political'].lower())
            cent = re.search('cent', prof['political'].lower())
            if dem:
                return 1
            if liberal:
                return 0
            if repub:
                return 3
            if cons:
                return 5
            if mod:
                return 4
            if cent:
                return 2
        else:
            return None

    def reddit_proxy(self, prof):
        if 'subs' in prof:
            for sub in prof['subs']:
                if 'apple' in sub['name'].lower():
                    return 4
                if 'the_donald' in sub['name'].lower():
                    return 5
                if 'crypto' in sub['name'].lower():
                    return 1
                if 'hacking' in sub['name'].lower():
                    return 0
                if 'politics' in sub['name'].lower():
                    return 2
                if 'news' in sub['name'].lower():
                    return 2
                if 'trees' in sub['name'].lower():
                    return 3
        else:
            return None

    def like_lookup(self, likes):
        for like in likes:
            apple = re.search('apple', like.lower())
            nsa = re.search('nsa', like.lower())
            hack = re.search('hack', like.lower())
            snowden = re.search('snowden', like.lower())
            books = re.search('book', like.lower())
            data = re.search('data', like.lower())
            if apple:
                return 4
            if nsa:
                return 5
            if hack:
                return 3
            if books:
                return 2
            if snowden:
                return 0
            if data:
                return 1
        else:
            return None

    def follow_lookup(self, twit):
        if twit.get('following'):
            for follow in twit['following']:
                apple = re.search('apple', follow['name'].lower())
                nsa = re.search('nsa', follow['name'].lower())
                hack = re.search('hack', follow['name'].lower())
                snowden = re.search('snowden', follow['name'].lower())
                books = re.search('book', follow['name'].lower())
                data = re.search('data', follow['name'].lower())
                if apple:
                    return 4
                if nsa:
                    return 5
                if hack:
                    return 3
                if books:
                    return 2
                if snowden:
                    return 0
                if data:
                    return 1
            else:
                return None
        return None

    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares
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
