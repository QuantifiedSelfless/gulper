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
            fd = open('./lib/processors/lib/companies.txt', 'r')
            raw = fd.read()
            fd.close()
            self.companies = raw.split('\n')
            self.logger.info("Loaded company names for analysis")
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

    def scan_pos_tokens(self, alltext, missing_ones, counts, quotes):
        wordlists = [self.healthwords, self.poswork]
        for wlist in wordlists:
            for token in wlist:
                for text in alltext:
                    if token in text:
                        quotes.append(text)
                        if token in counts:
                            counts[token] += 1
                        else:
                            counts[token] = 1
            if token not in counts:
                missing_ones.append(token)
            else:
                if token in missing_ones:
                    missing_ones.remove(token)

        return counts, quotes, missing_ones

    def scan_neg_tokens(self, alltext, counts, quotes):
        #use self.partywords, self.negwork, self.skepwords
        wordlists = [self.partywords, self.negwork, self.skepwords]
        for wlist in wordlists:
            for token in wlist:
                for text in alltext:
                    if token in text:
                        quotes.append(text)
                        if token in counts:
                            counts[token] += 1
                        else:
                            counts[token] = 1

        return counts, quotes

    def scan_neg_events(self, nevents, allevents):
        wordlists = [self.partywords]
        for wlist in wordlists:
            for token in wlist:
                for event in allevents:
                    if token in event['name'] or token in event['description']:
                        nevents.append(event['name'])
        return nevents

    def scan_pos_events(self, pevents, allevents):
        wordlists = [self.goodevents]
        for wlist in wordlists:
            for token in wlist:
                for event in allevents:
                    if token in event['name'] or token in event['description']:
                        pevents.append(event['name'])
        return pevents

    @gen.coroutine
    def process(self, user_data):
        interview_data = {}
        interview_data['name'] = user_data.name
        # Try counts on post tokens
        # tweets is list of str
        # fb text is list of dicts, need 'text'
        pos_counts = {}
        pos_quotes = []
        neg_counts = {}
        neg_quotes = []
        missing = set()
        if user_data.data.get('fbtext'):
            fb_text = [text['text'] for text in user_data.data['fbtext']]
            neg_counts, neg_quotes = self.scan_neg_tokens(
                fb_text, neg_counts, neg_quotes)
            pos_counts, pos_quotes, missing = self.scan_pos_tokens(
                fb_text, missing, pos_counts, pos_quotes)

        if user_data.data.get('twitter'):
            tweets = user_data.data['twitter']['tweets']
            neg_counts, neg_quotes = self.scan_neg_tokens(
                tweets, neg_counts, neg_quotes)
            pos_counts, pos_quotes, missing = self.scan_pos_tokens(
                tweets, missing, pos_counts, pos_quotes)

        # Try looking through likes and follows

        # Look through Events
        pos_events = []
        neg_events = []
        if user_data.data.get('fbevents'):
            events = [event for event in user_data.data['fbevents']['events']]
            pos_events = self.scan_pos_events(self, pos_events, events)
            neg_events = self.scan_neg_events(self, neg_events, events)

        # Try sub-reddits

        return True

    def save_user(self, data, user_data):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/interview/user/{}.json".format(user_data.userid)
            with open(filename, 'w+') as fd:
                json.dump(data, fd)
        else:
            blob_enc = user_data.encrypt_blob(data)
            filename = "./data/interview/user/{}.enc".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user(self, user):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/interview/user/{}.json".format(user.userid)
            with open(filename, 'r') as fd:
                return json.load(fd)
        else:
            filename = "./data/interview/user/{}.enc".format(user.userid)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    @gen.coroutine
    def interview_points(self, user, request):
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
            ('interview', self.interview_points),
        ]
