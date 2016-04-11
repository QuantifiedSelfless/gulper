from tornado import gen
from .lib.utils import process_api_handler
from ..config import CONFIG
from .lib.baseprocessor import BaseProcessor

import ujson as json
import re
import itertools
import random
import os


class TrackedProcessor(BaseProcessor):
    name = 'tracked_processor'

    def __init__(self):
        super().__init__()
        if not os.path.exists("./data/tracked/user"):
            os.makedirs("./data/interview/user")

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

    @gen.coroutine
    def process(self, user_data):
        # Generate some potential articles
        # Get some friends names
        # Add to the article.db

        self.logger.info("Processing user: {}".format(user_data.userid))
        first, last = self.user_name(user_data.name)

        tracking_data = {}
        tracking_data['messages'] = []
        names = []
        if user_data.data.get('gtext'):
            gpeople = itertools.chain.from_iterable(
                    user_data.data['gtext']['people'])
            cleaned = self.check_names(gpeople, last)
            names.append(cleaned)


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
            ('interview', self.tracking_messages),
        ]