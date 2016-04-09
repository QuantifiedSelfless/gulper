from tornado import gen
from ..config import CONFIG
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor

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
            fd = open('./lib/processors/lib/stopwords.txt', 'r')
            raw = fd.read()
            fd.close()
            self.stopwords = raw.split('\n')
            self.logger.info("Loaded stop words for analysis")
        except (IOError, ValueError):
            self.logger.info("Stop words not availble")
        try:
            fd = open('./lib/processors/lib/fakefacts.txt', 'r')
            raw = fd.read()
            fd.close()
            self.fakefacts = raw.split('\n')
        except (IOError, ValueError):
            self.logger.info("Couldn't find fake facts")
        try:
            fd = open('./lib/processors/lib/realfacts.txt', 'r')
            raw = fd.read()
            fd.close()
            self.realfacts = raw.split('\n')
        except (IOError, ValueError):
            self.logger.info("Couldn't find real facts")
        self.truths = random.randint(7, 8)

    def get_words(self, text_list):
        words = []
        for text in text_list:
            if text is None:
                continue
            words.extend(re.findall(r"[\w']+", text))
        lower = [word.lower() for word in words]
        return lower

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
        if total == 0:
            return 0
        count = 0
        for text in text_list:
            if word in text:
                count += 1
        return count/total

    def common_subreddit(self, subs):
        allsubs = []
        for sub in subs:
            allsubs.append(sub['subreddit'])
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
            me2 = re.search(lastname.lower(), name)
            if me or me2:
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
        lie = ''
        while len(lie) < 4:
            lie = random.choice(people)
        return person, lie

    def fill_truths(self, truestuff):
        while len(truestuff) < self.truths:
            truestuff.append(random.choice(self.realfacts))
        return truestuff

    def fill_lies(self, lies):
        while len(lies) < (15 - self.truths):
            lies.append(random.choice(self.fakefacts))
        return lies

    def percentage_check(self, word, text_list, thresh, fact_str, facts, lies):
        freq = self.get_percentage(word, text_list)
        if freq > thresh:
            if random.randint(0, 1) == 0 and len(facts) < 5:
                facts.append(
                    fact_str.format(round(freq * 100)))
            else:
                rand = 0
                while rand == 0:
                    rand = random.randint(-10, 10)
                lies.append(
                    fact_str.format(round(freq * 100 + rand)))
        return facts, lies

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

        if user_data.data['gtext'] is not False and user_data.data['gtext'] is not None:
            if user_data.data['gtext'].get('people', None) is not None:
                gpeople = itertools.chain.from_iterable(
                    user_data.data['gtext']['people'])
                cleaned = self.check_names(gpeople, user_data.name.split(' ')[-1])
                true, lie = self.common_email_contact(cleaned)
                if random.randint(0, 1) == 0:
                    truth_data['true'].append(
                        "Your most common gmail contact is {0}".format(true))
                else:
                    truth_data['false'].append(
                        "Your most common gmail contact is {0}".format(lie))
            gwords = self.get_words(user_data.data['gtext']['text'])
            gfreq = self.word_freq(gwords)
            if random.randint(0, 1) == 0:
                truth_data['true'].append(
                    "Besides articles, prepositions, and pronouns your most common word in email is {0}".format(gfreq[0][1]))
            else:
                word_len = len(gfreq)
                grab = round(word_len * .5)
                truth_data['false'].append(
                    "Besides articles, prepositions, and pronouns your most common word in email is \"{0}\"".format(gfreq[grab][1]))

        if user_data.data['fbtext'] is not False:
            text_list = [post['text'] for post in user_data.data['fbtext']['text']]
            fbwords = self.get_words(text_list)
            fbfreq = self.word_freq(fbwords)
            truth_data['true'], truth_data['false'] = self.percentage_check(
                    'me', text_list, .1,
                    "You use the word \"me\" in {0}\% of your facebook posts",
                    truth_data['true'], truth_data['false'])

            # freqme = self.get_percentage('me', text_list)
            # if freqme > .1:
            #     if random.randint(0, 1) == 0:
            #         truth_data['true'].append(
            #             "You use the word \"me\" in {0}\% of your facebook posts".format(round(freqme * 100)))
            #     else:
            #         rand = 0
            #         while rand == 0:
            #             rand = random.randint(-10, 10)
            #         truth_data['false'].append(
            #             "You use the word \"me\" in {0}\% of your facebook posts".format(round(freqme * 100 + rand)))
            freqfuck = self.get_percentage('fuck', text_list)
            if freqfuck > .05:
                if random.randint(0, 1) == 0:
                    truth_data['true'].append(
                        "You use the word \"fuck\" in {0}\% of your facebook posts".format(round(freqfuck * 100)))
                else:
                    rand = 0
                    while rand == 0:
                        rand = random.randint(-5, 10)
                    truth_data['false'].append(
                        "You use the word \"fuck\" in {0}\% of your facebook posts".format(round(freqfuck * 100 + rand)))
            yassquant = self.get_num_uses('yass', fbfreq)
            if yassquant > 5 and len(truth_data['true']) < 5:
                truth_data['true'].append(
                    "You used the word \"yass\" {0} times on facebook".format(
                        yassquant))
            dafuqquant = self.get_num_uses('dafuq', fbfreq)
            if dafuqquant > 5 and len(truth_data['true']) < 5:
                truth_data['true'].append(
                    "You used the word \"dafuq\" {0} times on facebook".format(
                        dafuqquant))
            lolquant = self.get_num_uses('lol', fbfreq)
            if lolquant > 3 and len(truth_data['false']) < 5:
                truth_data['false'].append(
                    "You used the word \"LOL\" {0} times on facebook".format(
                        lolquant + 25))

        if user_data.data['reddit'] is not False:
            fact, lie = self.common_subreddit(
                user_data.data['reddit']['submissions'])
            if (len(truth_data['true']) < len(truth_data['false'])):
                truth_data['true'].append(
                    "Your most common subreddit you submit to is {0}".format(
                        fact))
            else:
                truth_data['false'].append(
                    "Your most common subreddit you submit to is {0}".format(
                        lie))

        truth_data['true'] = self.fill_truths(truth_data['true'])
        truth_data['false'] = self.fill_lies(truth_data['false'])

        self.save_user(truth_data, user_data)
        self.logger.info("Saved truth game data")

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
            ('truth', self.truth_grab),
        ]
