from tornado import gen
from .lib.handler import process_api_handler
from .lib.baseprocessor import BaseProcessor

import re
import itertools
import random


class MirrorProcessor(BaseProcessor):
    name = 'mirror_processor'
    names = ['Amelia Bloom',
             'Don DeClair',
             'Lily Jordan',
             'Bo Rakenfold']
    max_names = 10

    def __init__(self):
        super().__init__()

    def user_name(self, name):
        names = name.split(' ')
        return names[0], names[-1]

    def check_names(self, names, lastname, my_email):
        """
        Check if it's an email address or self
        """
        good_names = []
        for name in names:
            email = re.search('@', name)
            me = re.search(lastname, name)
            mine = re.search(my_email, name)
            if email or me or mine:
                continue
            else:
                good_names.append(name)
        good_names = set(good_names)
        return list(good_names)

    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares
        """
        self.logger.info("Processing user: {}".format(user_data.userid))
        first, last = self.user_name(user_data.meta['name'])
        email = user_data.meta['email']

        mirror_data = {}
        mirror_data['name'] = user_data.meta['name']
        mirror_data['friends'] = []
        if user_data.data.get('gmail'):
            if user_data.data['gmail'].get('people'):
                gpeople = itertools.chain.from_iterable(
                    user_data.data['gmail']['people'])
                cleaned = self.check_names(gpeople, last, email)
                mirror_data['friends'].extend(cleaned)
            else:
                mirror_data['friends'] = self.names
        else:
            mirror_data['friends'] = self.names

        if len(mirror_data['friends']) > self.max_names:
            randos = []
            for i in range(10):
                choice = random.choice(mirror_data['friends'])
                randos.append(choice)
            mirror_data['friends'] = randos

        mirror_data['work'] = []
        if user_data.data['fbprofile']:
            profile = user_data.data['fbprofile']
            if 'work' in profile:
                for employ in profile['work']:
                    if 'employer' in employ:
                        mirror_data['work'].append(employ['employer']['name'])
                    else:
                        mirror_data['work'].append("DesignCraft")
            else:
                mirror_data['work'].append("DesignCraft")

        self.save_user_blob(mirror_data, user_data)

        self.logger.info("Saved mirror data")
        return True

    @gen.coroutine
    def mirror_stuff(self, user, request):
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
            ('mirror', self.mirror_stuff),
        ]
