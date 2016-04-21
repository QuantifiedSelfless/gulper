from tornado import gen
from .lib.handler import process_api_handler
from ..config import CONFIG
from .lib.baseprocessor import BaseProcessor

import re
import itertools
import random
import os


class TrackedProcessor(BaseProcessor):
    name = 'tracked_processor'

    def __init__(self):
        super().__init__()

    def user_name(self, name):
        names = name.split(' ')
        return names[0], names[-1]

    def check_names(self, names, lastname):
        """
        Check if it's an email address or self
        """
        good_names = []
        for name in names:
            email = re.search('@', name)
            me = re.search(lastname, name)
            if email or me:
                continue
            else:
                good_names.append(name)
        good_names = set(good_names)
        return list(good_names)

    def build_data(self, data, gppl, redppl, twitppl, fblikes, sphrases, cphrases, tphrase, rphrase, fphrase):
        data['messages'] = []
        if len(gppl) > 0:
            while len(sphrases) > 0:
                pers = random.choice(gppl)
                phr = sphrases.pop()
                phrc = cphrases.pop()
                makestr = "{0} {1} {2}".format(pers, phrc, phr)
                data['messages'].append(makestr)
        if len(redppl) > 0:
            pers = random.choice(redppl)
            makestr = "{0} {1}".format(pers, rphrase)
            data['messages'].append(makestr)
        if len(twitppl) > 0:
            pers = random.choice(twitppl)
            makestr = "{0} {1}".format(pers, tphrase)
            data['messages'].append(makestr)
        if len(fblikes) > 0:
            like = random.choice(fblikes)
            makestr = "{0} {1}".format(fphrase, like)
            data['messages'].append(makestr)
        return data


    @gen.coroutine
    def process(self, user_data):
        # Add to the article.db

        self.logger.info("Processing user: {}".format(user_data.userid))
        first, last = self.user_name(user_data.meta['name'])
        connecting_phrases = ["wants to share with you",
                              "wants to tell you about",
                              "wants you to check out"]
        share_phrases = ["a big update in life",
                         "an important update",
                         "some big news"]
        twitter_phrase = "has a tweet you may want to see!"
        reddit_phrase = "has something interesting for you on reddit."
        fb_phrase = "Facebook has some updates for you about"

        tracking_data = {}
        names = []
        if user_data.data.get('gmail'):
            gmail = user_data.data['gmail']
            if gmail.get('people'):
                people_flat = itertools.chain.from_iterable(gmail['people'])
                cleaned = self.check_names(people_flat, last)
                names.extend(cleaned)

        red_friends = []
        if user_data.data.get('reddit'):
            if len(user_data.data['reddit']['text']):
                rtext = user_data.data['reddit']['text']
                red_friends = [text['author'] 
                               for text in rtext if text.get('author')]

        follows = []
        if user_data.data.get('twitter'):
            follows = [f['name'] for f in user_data.data['twitter']['following']]

        likes = []
        if user_data.data.get('fblikes'):
            if len(user_data.data['fblikes']['likes']) > 0:
                likes = [like for like in user_data.data['fblikes']['likes']]

        tracking_data = self.build_data(tracking_data, names,
                                        red_friends, follows, likes, share_phrases,
                                        connecting_phrases, twitter_phrase,
                                        reddit_phrase, fb_phrase)
        if len(tracking_data['messages']) < 1:
            return False
        else:
            self.save_user_blob(tracking_data, user_data)
            return True

    @gen.coroutine
    def tracking_messages(self, user, request):
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
            ('tracking', self.tracking_messages),
        ]
