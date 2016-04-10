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
            self.healthwords = raw.split('\n')
            self.logger.info("Loaded company names for analysis")
        except (IOError, ValueError):
            self.logger.info("No company names loaded")

    @gen.coroutine
    def process(self, user_data):

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
