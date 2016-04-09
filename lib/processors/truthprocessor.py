from tornado import gen
from ..config import CONFIG
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor

from collections import Counter
import ujson as json
import itertools
import re
import random
import os


class TruthProcessor(BaseProcessor):
    name = 'truth_processor'
    data = {}

    def __init__(self):
        super().__init__()
        if not os.path.exists("./data/truth/user"):
            os.makedirs("./data/truth/user")

        try:
            fd = open('lib/stopwords.txt', 'r')
            raw = fd.read()
            fd.close()
            self.stopwords = raw.split('\n')
            self.logger.info("Loaded stop words for analysis")
        except (IOError, ValueError):
            self.logger.info("Stop words not availble")
        try:
            fd = open('lib/fakefacts.txt', 'r')
            raw = fd.read()
            fd.close()
            self.fakefacts = raw.split('\n')
        except (IOError, ValueError):
            self.logger.info("Couldn't find fake facts")
        try:
            fd = open('lib/realfacts.txt', 'r')
            raw = fd.read()
            fd.close()
            self.realfacts = raw.split('\n')
        except (IOError, ValueError):
            self.logger.info("Couldn't find real facts")

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

    def get_num_uses(self, word, wordfreq):
        for word in wordfreq:
            if word[1] == word:
                return word[0]
        return 0

    def get_percentage(self, word, text_list):
        total = float(len(text_list))
        count = 0
        for text in text_list:
            words = text.split()
            if word in text:
                count += 1
        return count/total

    def common_subreddit(self, subs):
        allsubs = []
        for sub in subs:
            allsubs.append(sub)
        highest = 0
        the_one = None
        for sub in allsubs:
            total = allsubs.count(sub)
            if total > highest:
                highest = total
                the_one = sub
        unique = set(allsubs)
        allsubs = list(unique)
        allsubs.remove(the_one)
        lie = random.choice(allsubs)
        return the_one, lie

    def check_names(self, names, lastname):
        """
        Check if it's an email address or self
        """
        good_names = []
        for name in names:
            me = re.search(lastname, name)
            if me:
                continue
            else:
                good_names.append(name)
        return good_names

    def common_email_contact(self, people):
        highest = 0
        person = None
        for name in people:
            total = people.count(name)
            if total > highest:
                highest = total
                person = name
        unique = set(people)
        people = list(unique)
        people.remove(person)
        lie = random.choice(person)
        return person, lie

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
        - Times said Worst
        - Times said Best
        - Comment karma
        - Twitter
        - Swear words
        - times saying 'me'
        """
        truth_data = {}
        truth_data['name'] = user_data.name
        truth_data['true'] = []
        truth_data['false'] = []

        if user_data['gtext'] is not False:
            gpeople = itertools.chain.from_iterable(
                user_data['gtext']['people'])
            cleaned = self.check_names(gpeople)
            true, lie = self.common_email_contact(cleaned)
            if random.randint(0, 1) == 0:
                truth_data['true'].append(
                    "Your most common gmail contact is {0}".format(true))
            else:
                truth_data['false'].append(
                    "Your most common gmail contact is {0}".format(lie))


    def save_user(self, data, user_data):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/truth/user/{}.json".format(user_data.userid)
            with open(filename, 'w+') as fd:
                json.dump(data, fd)
        else:
            blob_enc = user_data.encrypt_blob(data)
            filename = "./data/truth/user/{}.enc".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user(self, user):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/truth/user/{}.json".format(user.userid)
            with open(filename, 'r') as fd:
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