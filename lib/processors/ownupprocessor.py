from tornado import gen
import traceback
import ujson as json

from ..config import CONFIG
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


class OwnupProcessor(BaseProcessor):
    name = 'ownup'
    limit = 10
    keywords = ["think", "perspective", "opinion", "view", "election", "politics", "president", "democrat", "liberal", "republican", "correct", "liar", "truth", "country", "united states", "america", "usa", "awkward", "story", "school", "when", "then", "kill", "cute", "beer", "party", "alcohol", "media", "congress", "lesbian", "gay", "queer", "bisexual", "transexual", "favorite", "tax", "climate change", "technology", "apple", "google", "caucus", "environment", "justice", "trump", "sanders", "clinton", "social", "black lives matter", "bln", "slavery"]

    def is_great_quote(self, text):
        text = text.lower()
        for word in self.keywords:
            if text.find(word) > 0:
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
            elif len(sentence) > 5:
                temp.append(sentence)
        return True

    def process_facebook(self, user_data, temp, perm):
        try:
            fbtext = user_data.data.get('fbtext')
            if not fbtext or len(perm) >= self.limit:
                return
            fbposts = fbtext['text']
            for post in fbposts:
                if not self.process_post(post['text'], temp, perm):
                    return
        except Exception as ex:
            print('[OU] Exception occurred when processing facebook data.')
            print(ex)
            traceback.print_exc()

    def process_twitter(self, user_data, temp, perm):
        try:
            twitter = user_data.data.get('twitter')
            if not twitter or len(perm) >= self.limit:
                return
            tweets = twitter['tweets']
            for post in tweets:
                if not self.process_post(post, temp, perm):
                    return
        except Exception as ex:
            print('[OU] Exception occured when processing twitter data.')
            print(ex)
            traceback.print_exc()

    def process_reddit(self, user_data, temp, perm):
        try:
            reddit = user_data.data.get('reddit')
            if not reddit or len(perm) >= self.limit:
                return
            print(reddit.keys())
            posts = reddit['text']
            for post in posts:
                if not self.process_post(post['body'], temp, perm):
                    return
        except Exception as ex:
            print('[OU] Exception occured when processing reddit data.')
            print(ex)
            traceback.print_exc()
    
    def process_gtext(self, user_data, temp, perm):
        try:
            gtext = user_data.data.get('gtext')
            if not gtext or len(perm) >= self.limit:
                return
            posts = gtext['snippets']
            for post in posts:
                if not self.process_post(post, temp, perm):
                    return
        except Exception as ex:
            print('[OU] Exception occured when processing gmail data.')
            print(ex)
            traceback.print_exc()
 
    @gen.coroutine
    def process(self, user_data):
        self.logger.info("[OU] Processing user: {}".format(user_data.userid))
        userid = user_data.userid
        temp = []
        perm = []
        self.process_facebook(user_data, temp, perm)
        self.process_twitter(user_data, temp, perm)
        self.process_reddit(user_data, temp, perm)
        self.process_gtext(user_data, temp, perm)
        while len(perm) < self.limit and len(temp) > 1:
            perm.append(temp.pop())
        if len(perm) <= 0:
            return False
        self.save_user(perm, user_data)
        return True

    def save_user(self, data, user_data):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/ownup/user/{}.json".format(user_data.userid)
            with open(filename, 'w+') as fd:
                json.dump(data, fd)
        else:
            blob_enc = user_data.encrypt_blob(data)
            filename = "./data/ownup/user/{}.enc".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user(self, user):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/ownup/user/{}.json".format(user.userid)
            with open(filename, 'rb') as fd:
                return json.load(fd)
        else:
            filename = "./data/ownup/user/{}.enc".format(user.userid)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    @gen.coroutine
    def get(self, user, request):
        try:
            return self.load_user(user)
        except Exception as ex:
            return "Data for this user is not available."

    @process_api_handler
    def register_handlers(self):
        return [
            ('quotes', self.get),
        ]
