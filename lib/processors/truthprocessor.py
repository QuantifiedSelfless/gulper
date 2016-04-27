from tornado import gen
from .lib.handler import process_api_handler
from .lib.baseprocessor import BaseProcessor

import itertools
import re
import random
from collections import Counter


class TruthProcessor(BaseProcessor):
    name = 'truth_processor'
    data = {}
    num_items = 100

    def __init__(self):
        super().__init__()
        self.stopwords = self.load_keywords("stopwords.txt")
        self.fakefacts = self.load_keywords("fakefacts.txt")
        self.realfacts = self.load_keywords("realfacts.txt")
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
        for wordf in wordfreq:
            if wordf[1] == word:
                return wordf[0]
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
        return self._common_and_lie(allsubs)

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
        return self._common_and_lie(people)

    def _common_and_lie(self, items):
        items_count = Counter(items)
        top_10 = items_count.most_common(10)
        best_item, _ = top_10[0]
        lie, _ = random.choice(top_10[1:])
        return best_item, lie

    def percentage_check(self, word, text_list, thresh, fact_str, facts, lies):
        freq = self.get_percentage(word, text_list)
        if freq > thresh:
            if random.randint(0, 1) == 0 and len(facts) <= 5:
                facts.append(
                    fact_str.format(round(freq * 100)))
            else:
                rand = 0
                while rand == 0:
                    rand = random.randint(-(thresh*10), thresh*10)
                lies.append(
                    fact_str.format(round(freq * 100 + rand)))
        return facts, lies

    def check_uses(self, word, freq, thresh, fact_str, facts, lies, which):
        quant = self.get_num_uses(word, freq)
        if which == 0:
            if quant >= thresh and len(facts) <= self.truths:
                facts.append(
                    fact_str.format(quant))
        else:
            if quant >= thresh and len(lies) <= 15 - self.truths:
                lies.append(
                    fact_str.format(quant * random.randint(round(thresh/3),
                                                           thresh*3)))
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
        truth_data['name'] = user_data.meta['name']
        truth_data['true'] = []
        truth_data['false'] = []

        if user_data.data.get('gmail'):
            if user_data.data['gmail'].get('people') is not None:
                try:
                    gpeople = itertools.chain.from_iterable(
                        user_data.data['gmail']['people'])
                    cleaned = self.check_names(
                        gpeople,
                        user_data.meta['name'].rsplit(' ', 1)[-1]
                    )
                    true, lie = self.common_email_contact(cleaned)
                    if random.randint(0, 1) == 0:
                        truth_data['true'].append(
                            "Your most common gmail contact is {0}".format(true))
                    else:
                        truth_data['false'].append(
                            "Your most common gmail contact is {0}".format(lie))
                except IndexError:
                    pass
            if user_data.data['gmail'].get('text'):
                gwords = self.get_words(user_data.data['gmail']['text'])
                gfreq = self.word_freq(gwords)
                if len(gfreq) > 0:
                    if random.randint(0, 1) == 0:
                        truth_data['true'].append(
                            "Besides articles, prepositions, and pronouns your most "
                            "common word in email is {0}".format(gfreq[0][1]))
                    else:
                        word_len = len(gfreq)
                        grab = round(word_len * .5)
                        truth_data['false'].append(
                            "Besides articles, prepositions, and pronouns your most "
                            "common word in email is \"{0}\"".format(gfreq[grab][1]))

        if user_data.data.get('fbtext'):
            text_list = [post['text']
                         for post in user_data.data['fbtext']['text']]
            fbwords = self.get_words(text_list)
            fbfreq = self.word_freq(fbwords)
            # Later this can be a loop that tried different word, token pairs
            truth_data['true'], truth_data['false'] = self.percentage_check(
                    'me', text_list, .1,
                    "You use the word \"me\" in {0}% of your facebook posts",
                    truth_data['true'], truth_data['false'])
            truth_data['true'], truth_data['false'] = self.percentage_check(
                    'fuck', text_list, .05,
                    "You use the word \"fuck\" in {0}% of your facebook posts",
                    truth_data['true'], truth_data['false'])
            # Now going to get into checking number of word uses
            truth_data['true'], truth_data['false'] = self.check_uses(
                    'yass', fbfreq, 5,
                    "You used the word \"yass\" {0} times on facebook",
                    truth_data['true'], truth_data['false'], 0)
            truth_data['true'], truth_data['false'] = self.check_uses(
                    'dafuq', fbfreq, 5,
                    "You used the word \"dafuq\" {0} times on facebook",
                    truth_data['true'], truth_data['false'], 0)
            truth_data['true'], truth_data['false'] = self.check_uses(
                    'lol', fbfreq, 5,
                    "You used the word \"LOL\" {0} times on facebook",
                    truth_data['true'], truth_data['false'], 1)
            truth_data['true'], truth_data['false'] = self.check_uses(
                    'love', fbfreq, 5,
                    "You used the word \"love\" {0} times on facebook",
                    truth_data['true'], truth_data['false'], 0)

        if user_data.data.get('reddit'):
            try:
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
            except IndexError:
                pass

        random.shuffle(truth_data['true'])
        random.shuffle(truth_data['false'])
        truth_data['true'] = truth_data['true'][:self.num_items]
        truth_data['false'] = truth_data['false'][:self.num_items]

        self.save_user_blob(truth_data, user_data)
        self.logger.info("Saved truth game data")

        # Need to make final determination on whether we want to use
        # real world facts. If we are, we can let everyone play
        return True

    @gen.coroutine
    def truth_grab(self, user, request):
        """
        Returns relevant data that the exhibits may want to know
        """
        data = self.load_user_blob(user)
        if len(data['true']) > 10:
            data['true'] = random.sample(data['true'], 10)
        if len(data['false']) > 10:
            data['false'] = random.sample(data['false'], 10)
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
