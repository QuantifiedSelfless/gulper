from tornado import gen
from .lib.utils import process_api_handler
from ..config import CONFIG
from .lib.baseprocessor import BaseProcessor

import ujson as json
import re
import itertools
import random
import os

class InterviewProcessor(BaseProcessor):
    name = 'interview_processor'

    def __init__(self):
        super().__init__()
        if not os.path.exists("./data/interview/user"):
            os.makedirs("./data/interview/user")

        try:
            fd = open('./lib/processors/lib/negativeworkwords.txt', 'r')
            raw = fd.read()
            fd.close()
            self.negwork = raw.split('\n')
            self.logger.info("Loaded negative work words for analysis")
        except (IOError, ValueError):
            self.logger.info("No Negative work words loaded")
        try:
            fd = open('./lib/processors/lib/positiveworkwords.txt', 'r')
            raw = fd.read()
            fd.close()
            self.poswork = raw.split('\n')
            self.logger.info("Loaded positive work words for analysis")
        except (IOError, ValueError):
            self.logger.info("No positive work words loaded")
        try:
            fd = open('./lib/processors/lib/partywords.txt', 'r')
            raw = fd.read()
            fd.close()
            self.partywords = raw.split('\n')
            self.logger.info("Loaded party words for analysis")
        except (IOError, ValueError):
            self.logger.info("No party words loaded")
        try:
            fd = open('./lib/processors/lib/healthwords.txt', 'r')
            raw = fd.read()
            fd.close()
            self.healthwords = raw.split('\n')
            self.logger.info("Loaded health words for analysis")
        except (IOError, ValueError):
            self.logger.info("No health words loaded")
        try:
            fd = open('./lib/processors/lib/skepticwords.txt', 'r')
            raw = fd.read()
            fd.close()
            self.skepwords = raw.split('\n')
            self.logger.info("Loaded skeptical words for analysis")
        except (IOError, ValueError):
            self.logger.info("No skepetical words loaded")
        try:
            fd = open('./lib/processors/lib/posinterests.txt', 'r')
            raw = fd.read()
            fd.close()
            self.posinterests = raw.split('\n')
            self.logger.info("Loaded positive interests for analysis")
        except (IOError, ValueError):
            self.logger.info("No company names loaded")
        try:
            fd = open('./lib/processors/lib/goodevents.txt', 'r')
            raw = fd.read()
            fd.close()
            self.posevents = raw.split('\n')
            self.logger.info("Loaded good events for analysis")
        except (IOError, ValueError):
            self.logger.info("No good events loaded")

    def scan_pos_tokens(self, alltext, counts, quotes):
        wordlists = [self.healthwords, self.poswork]
        for wlist in wordlists:
            for token in wlist:
                for text in alltext:
                    if token.lower() in text.lower():
                        quotes.append(text)
                        if token in counts:
                            counts[token] += 1
                        else:
                            counts[token] = 1

        return counts, quotes

    def scan_neg_tokens(self, alltext, counts, quotes):
        wordlists = [self.partywords, self.negwork, self.skepwords]
        for wlist in wordlists:
            for token in wlist:
                for text in alltext:
                    if token.lower() in text.lower():
                        quotes.append(text)
                        if token in counts:
                            counts[token] += 1
                        else:
                            counts[token] = 1

        return counts, quotes

    def scan_neg_events(self, nevents, allevents):
        wordlists = [self.partywords, self.negwork]
        for wlist in wordlists:
            for token in wlist:
                for event in allevents:
                    if token.lower() in event['name'].lower() or token.lower() in event['description'].lower():
                        nevents.append(event['name'])
        return nevents

    def scan_pos_events(self, pevents, allevents):
        wordlists = [self.posevents, self.posinterests]
        for wlist in wordlists:
            for token in wlist:
                for event in allevents:
                    if token.lower() in event['name'].lower() or token.lower() in event['description'].lower():
                        pevents.append(event['name'])
        return pevents

    def scan_neg_interests(self, nints, interests):
        wordlists = [self.skepwords, self.partywords, self.negwork]
        for wlist in wordlists:
            for token in wlist:
                for interest in interests:
                    if token.lower() in interest.lower():
                        nints.append(interest)
        return nints

    def scan_pos_interests(self, pints, interests):
        wordlists = [self.posinterests, self.posevents, self.healthwords]
        for wlist in wordlists:
            for token in wlist:
                for interest in interests:
                    if token.lower() in interest.lower():
                        pints.append(interest)
        return pints

    def build_data(self, intdata, pquote, nquote, pcount, ncount, pint, nint, pevent, nevent):
        intdata['pros'] = []
        intdata['cons'] = []
        if len(pcount.keys()) > 0:
            srt = sorted(pcount, key=pcount.get)
            gkey = srt[-1]
            makestr = "said {0} {1} times".format(gkey, pcount[gkey])
            intdata['pros'].append(makestr)
        if len(ncount.keys()) > 0:
            srt = sorted(ncount, key=ncount.get)
            gkey = srt[-1]
            makestr = "said {0} {1} times".format(gkey, ncount[gkey])
            intdata['cons'].append(makestr)
        if len(pquote) > 0:
            makestr = "once said '{0}'".format(random.choice(pquote))
            intdata['pros'].append(makestr)
        if len(nquote) > 0:
            makestr = "once said '{0}'".format(random.choice(nquote))
            intdata['cons'].append(makestr)
        if len(pint) > 0:
            makestr = "is interested in {0}".format(random.choice(pint))
            intdata['pros'].append(makestr)
        if len(nint) > 0:
            makestr = "is interested in {0}".format(random.choice(nint))
            intdata['cons'].append(makestr)
        if len(pevent) > 0:
            makestr = "went to '{0}' event".format(random.choice(pevent))
            intdata['pros'].append(makestr)
        if len(nevent) > 0:
            makestr = "went to '{0}' event".format(random.choice(nevent))
            intdata['cons'].append(makestr)

        return intdata

    @gen.coroutine
    def process(self, user_data):
        interview_data = {}
        interview_data['name'] = user_data.meta['name']
        # Try counts on post tokens
        # tweets is list of str
        # fb text is list of dicts, need 'text'
        pos_counts = {}
        pos_quotes = []
        neg_counts = {}
        neg_quotes = []
        if user_data.data.get('fbtext'):
            fb_text = [text['text'] for text in user_data.data['fbtext']['text']]
            neg_counts, neg_quotes = self.scan_neg_tokens(
                fb_text, neg_counts, neg_quotes)
            pos_counts, pos_quotes = self.scan_pos_tokens(
                fb_text, pos_counts, pos_quotes)

        pos_interests = []
        neg_interests = []
        if user_data.data.get('twitter'):
            tweets = user_data.data['twitter']['tweets']
            neg_counts, neg_quotes = self.scan_neg_tokens(
                tweets, neg_counts, neg_quotes)
            pos_counts, pos_quotes = self.scan_pos_tokens(
                tweets, pos_counts, pos_quotes)
            following = [follow['name'] for follow in user_data.data['twitter']['following']]
            neg_interests = self.scan_neg_interests(
                neg_interests, following)
            pos_interests = self.scan_pos_interests(
                pos_interests, following)

        pos_events = []
        neg_events = []
        if user_data.data.get('fbevents'):
            events = [event for event in user_data.data['fbevents']['events']]
            pos_events = self.scan_pos_events(pos_events, events)
            neg_events = self.scan_neg_events(neg_events, events)

        if user_data.data.get('reddit'):
            subs = [sub['name'] for sub in user_data.data['reddit']['subs']]
            neg_interests = self.scan_neg_interests(
                neg_interests, subs)
            pos_interests = self.scan_pos_interests(
                pos_interests, subs)

        if user_data.data.get('fblikes'):
            likes = user_data.data['fblikes']
            neg_interests = self.scan_neg_interests(
                neg_interests, likes)
            pos_interests = self.scan_pos_interests(
                pos_interests, likes)

        testit = pos_quotes + neg_quotes + pos_interests + neg_interests + pos_events + neg_events
        if len(testit) <= 2:
            return False

        interview_data = self.build_data(interview_data, pos_quotes, neg_quotes,
                                pos_counts, neg_counts, pos_interests,
                                neg_interests, pos_events, neg_events)

        self.logger.info("Successfully processed data for User %s" % user_data.userid)
        self.save_user_blob(interview_data, user_data)
        return True

    @gen.coroutine
    def interview_points(self, user, request):
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
            ('interview', self.interview_points),
        ]
