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
        self.stopwords = set(self.load_keywords("stopwords.txt"))
        self.fakefacts = self.load_keywords("fakefacts.txt")
        self.realfacts = self.load_keywords("realfacts.txt")
        self.emowords = self.load_keywords("mentalwords.txt")
        self.partywords = self.load_keywords("partywords.txt")
        self.healthwords = self.load_keywords("healthwords.txt")
        self.poswork = self.load_keywords("positiveworkwords.txt")

    def get_words(self, text_list):
        for text in text_list:
            if text:
                words = re.findall(r"\b[\w']+\b", text.lower())
                yield from words

    def word_freq(self, wordlist):
        cleanwords = [w for w in wordlist if w not in self.stopwords]
        return Counter(cleanwords)

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

    def percentage_check(self, freqmap, N):
        str_build = "You use the word '{0}' in approximately {1}% of your facebook posts"
        new_facts = []
        new_lies = []
        words = self.partywords + self.emowords
        for word in words:
            if word in freqmap:
                freq = freqmap[word] / float(N)
                if freq < .05:
                    continue
                if random.randint(0, 1) == 0:
                    new_facts.append(
                        str_build(word, round(freq * 100)))
                else:
                    rand = 0
                    while rand == 0:
                        rand = random.randint(-(freq*80), freq*200)
                        new_lies.append(
                            str_build.format(word, round(freq * 100 + rand)))
        return new_facts, new_lies

    def check_uses(self, freqmap):
        str_build = "You use the word '{0}' at least {1}% on Facebook"
        new_facts = []
        new_lies = []
        words = self.partywords + self.emowords + self.healthwords + self.poswork
        for word in words:
            if word in freqmap:
                freq = freqmap[word]
                if freq < 5:
                    continue
                if random.randint(0, 1) == 0:
                    new_facts.append(
                        str_build.format(word, freq))
                else:
                    rand = 0
                    while rand == 0:
                        rand = random.randint(-round(freq*.8), freq*3)
                        new_lies.append(
                            str_build.format(word, freq + rand))
        return new_facts, new_lies

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
                if gfreq:
                    if random.randint(0, 1) == 0:
                        most_common = gfreq.most_common(1)
                        truth_data['true'].append(
                            "Besides articles, prepositions, and pronouns your most "
                            "common word in email is {0}".format(most_common[0][0]))
                    else:
                        fake = random.choice(list(gfreq.keys()))
                        truth_data['false'].append(
                            "Besides articles, prepositions, and pronouns your most "
                            "common word in email is \"{0}\"".format(fake))

        if user_data.data.get('fbtext') and user_data.data['fbtext']['text']:
            text_list = (post['text']
                         for post in user_data.data['fbtext']['text'])
            N = len(user_data.data['fbtext']['text'])
            fbwords = self.get_words(text_list)
            fbfreq = self.word_freq(fbwords)
            # Later this can be a loop that tried different word, token pairs
            if fbfreq:
                if random.randint(0, 1) == 0:
                    most_common = fbfreq.most_common(1)
                    truth_data['true'].append(
                            "Besides articles, prepositions, and pronouns your most "
                            "common word on Facebook is {0}".format(most_common[0][0]))
                else:
                    fake = random.choice(list(fbfreq.keys()))
                    truth_data['true'].append(
                            "Besides articles, prepositions, and pronouns your most "
                            "common word on Facebook is {0}".format(fake))

                new_facts, new_lies = self.percentage_check(fbfreq, N)
                truth_data['true'] += new_facts
                truth_data['false'] += new_lies
                new_facts, new_lies = self.check_uses(fbfreq)
                truth_data['true'] += new_facts
                truth_data['false'] += new_lies


        if user_data.data.get('reddit'):
            try:
                fact, lie = self.common_subreddit(
                    user_data.data['reddit']['submissions'])
                if (len(truth_data['true']) <= len(truth_data['false'])):
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
        self.logger.info("True: %d, False: %d", len(truth_data['true']), len(truth_data['false']))
        if len(truth_data['true']) < 8:
            missing = 8 - len(truth_data['true'])
            truth_data['true'] += random.sample(
                self.realfacts, missing)
        if len(truth_data['false']) < 8:
            missing = 8 - len(truth_data['false'])
            truth_data['false'] += random.sample(
                self.fakefacts, missing)

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
        rando = random.randint(0, 1)
        if rando == 1:
            if len(data['true']) > 7:
                data['true'] = random.sample(data['true'], 7)
            if len(data['false']) > 8:
                data['false'] = random.sample(data['false'], 8)
        else:
            if len(data['true']) > 8:
                data['true'] = random.sample(data['true'], 8)
            if len(data['false']) > 7:
                data['false'] = random.sample(data['false'], 7)
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
