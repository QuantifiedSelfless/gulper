from tornado import gen
import traceback
import ujson as json

from ..config import CONFIG
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


class MentalHealthProcessor(BaseProcessor):
    name = 'mental_health'
    limit = 200
    keywords = ["concerned", "important", "love", "confused", "boredom", "greed", "amazing", "enjoyable", "terrible", "angry", "corrupt", "fun", "happiness", "comfort", "shitty", "nothing", "sharing", "privileged", "lucky", "grateful", "difficult", "impossible", "unfair", "exciting", "better", "worse", "upsetting", "easy", "boredom", "confusion", "pride", "confidence", "doubt", "fear", "disappointment", "diligence", "excitement", "sad", "interesting", "sexy", "love", "hate", "anxiety", "anger", "annoyance", "frustration", "empathy", "sympathy", "apathy", "concern", "sadness", "confusion", "condemnation", "anxiety", "enjoyment", "graciousness", "love", "hate", "impatience", "patience"]

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
        try:
            fbtext = user_data.data.get('fbtext')
            if not fbtext or len(quotes) >= self.limit:
                return
            fbposts = fbtext['text']
            for post in fbposts:
                if not self.process_post(post['text'], quotes):
                    return
        except Exception as ex:
            print('[MH] Exception occurred when processing facebook data.')
            print(ex)
            traceback.print_exc()

    def process_twitter(self, user_data, quotes):
        try:
            twitter = user_data.data.get('twitter')
            if not twitter or len(quotes) >= self.limit:
                return
            tweets = twitter['tweets']
            for post in tweets:
                if not self.process_post(post, quotes):
                    return
        except Exception as ex:
            print('[MH] Exception occured when processing twitter data.')
            print(ex)
            traceback.print_exc()

    def process_reddit(self, user_data, quotes):
        try:
            reddit = user_data.data.get('reddit')
            if not reddit or len(quotes) >= self.limit:
                return
            print(reddit.keys())
            posts = reddit['text']
            for post in posts:
                if not self.process_post(post['body'], quotes):
                    return
        except Exception as ex:
            print('[MH] Exception occured when processing reddit data.')
            print(ex)
            traceback.print_exc()
    
    def process_gtext(self, user_data, quotes):
        try:
            gtext = user_data.data.get('gtext')
            if not gtext or len(quotes) >= self.limit:
                return
            posts = gtext['snippets']
            for post in posts:
                if not self.process_post(post, quotes):
                    return
        except Exception as ex:
            print('[MH] Exception occured when processing gmail data.')
            print(ex)
            traceback.print_exc()
 
    @gen.coroutine
    def process(self, user_data):
        self.logger.info("[MH] Processing user: {}".format(user_data.userid))
        userid = user_data.userid
        quotes = []
        self.process_facebook(user_data, quotes)
        self.process_twitter(user_data, quotes)
        self.process_reddit(user_data, quotes)
        self.process_gtext(user_data, quotes)
        print(quotes)
        if len(quotes) < 0:
            return False
        self.save_user(quotes, user_data)
        return True

    def save_user(self, data, user_data):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/mentalhealth/user/{}.json".format(user_data.userid)
            with open(filename, 'w+') as fd:
                json.dump(data, fd)
        else:
            blob_enc = user_data.encrypt_blob(data)
            filename = "./data/mentalhealth/user/{}.enc".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user(self, user):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/mentalhealth/user/{}.json".format(user.userid)
            with open(filename, 'rb') as fd:
                return json.load(fd)
        else:
            filename = "./data/mentalhealth/user/{}.enc".format(user.userid)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    @gen.coroutine
    def get(self, user, request):
        print('A')
        print(self)
        print(self.get_argument('userid'))
        try:
            return self.load_user(user)
        except Exception as ex:
            return "Data for this user is not available."

    @process_api_handler
    def register_handlers(self):
        return [
            ('quotes', self.get),
        ]
