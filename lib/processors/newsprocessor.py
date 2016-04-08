from tornado import gen
from .utils import process_api_handler
from ..config import CONFIG

import re
import random
import ujson as json


class NewsProcessor(object):
    name = 'news_processor'

    def fb_proxy(self, prof):
        if 'political' in prof:
            dem = re.search('dem', prof['political'])
            liberal = re.search('liberal', prof['political'])
            repub = re.search('repub', prof['political'])
            cons = re.search('conservative', prof['political'])
            if dem:
                return 2
            if liberal:
                return 1
            if repub:
                return 3
            if cons:
                return 5
        else:
            return None

    def reddit_proxy(self, prof):
        if 'subs' in prof:
            for sub in prof['subs']:
                if sub['name'] == 'apple':
                    return 4
                if sub['name'] == 'the_donald':
                    return 5
                if sub['name'] == 'crypto':
                    return 1
                if sub['name'] == 'hacking':
                    return 0
                if sub['name'] == 'politics':
                    return 2
                if sub['name'] == 'news':
                    return 2
                if sub['name'] == 'trees':
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

    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares
        """
        data = {}
        data['category'] = None
        if user_data['fbprofile'] is not False:
            data['category'] = self.fb_proxy(user_data['fbprofile'])
        if data['category'] is None:
            if user_data['reddit'] is not False:
                data['category'] = self.reddit_proxy(user_data['reddit'])
        if data['category'] is None:
            if user_data['fblikes'] is not False:
                data['category'] = self.like_lookup(user_data['fblikes'])
        if data['category'] is None:
            if user_data['twitter'] is not False:
                data['category'] = self.follow_lookup(user_data['twitter'])
        if data['category'] is None:
            data['cateogry'] = random.randint(0, 5)
        self.save_user(data, user_data)

    def save_user(self, data, user_data):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/news/user/{}.json".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                json.dump(data, fd)
        else:
            blob_enc = user_data.encrypt_blob(data)
            filename = "./data/news/user/{}.enc".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user(self, user):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/news/user/{}.json".format(user.userid)
            with open(filename, 'rb') as fd:
                return json.load(fd)
        else:
            filename = "./data/news/user/{}.enc".format(user.userid)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    @gen.coroutine
    def get_category(self, user, request):
        """
        Returns relevant data that the exhibits may want to know
        """
        data = self.load_user(user)
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
