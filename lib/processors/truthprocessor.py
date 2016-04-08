from tornado import gen
from ..config import CONFIG
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor

from collections import Counter
import ujson as json
import itertools
import re


class TruthProcessor(BaseProcessor):
    name = 'truth_processor'
    data = {}

    def __init__(self):
        super().__init__()
        try:
            fd = open('lib/stopwords.txt', 'r')
            raw = fd.read()
            fd.close()
            self.stopwords = raw.split('\n')
            self.logger.info("Loaded stop words for analysis")
        except (IOError, ValueError):
            self.logger.info("Stop words not availble")

    def get_words(self, text_list):
        words = []
        for text in text_list:
            words.extend(re.findall(r"[\w']+", words))

    def word_freq(self, wordlist):
        cleanwords = [w for w in wordlist if w not in self.stopwords]
        wordfreq = [wordlist.count(p) for p in cleanwords]
        freqdict = dict(zip(cleanwords, wordfreq))
        aux = [(freqdict[key], key) for key in freqdict]
        aux.sort()
        aux.reverse()
        return aux

    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares
        """

        """
        Stuff to try:
        - Most often liked subreddit
        - Most liked stuff
        - Political Stuff (ie, how political are you)
        - Common words
        - Time said Worst
        - Times said Best
        """
        truth_data = {}
        truth_data['name'] = user_data.name
        truth_data['true'] = []
        truth_data['false'] = []

    def save_user(self, data, user_data):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/truth/user/{}.json".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                json.dump(data, fd)
        else:
            blob_enc = user_data.encrypt_blob(data)
            filename = "./data/truth/user/{}.enc".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user(self, user):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/truth/user/{}.json".format(user.userid)
            with open(filename, 'rb') as fd:
                return json.load(fd)
        else:
            filename = "./data/truth/user/{}.enc".format(user.userid)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    @gen.coroutine
    def truth_grab(self, user, request):
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
            ('truth', self.truth_grab,
        ]