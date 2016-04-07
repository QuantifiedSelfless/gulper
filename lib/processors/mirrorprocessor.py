from tornado import gen
from .utils import process_api_handler
from .lib.db import get_user
from ..config import CONFIG

import ujson as json
import re
import itertools
import random


class MirrorProcessor(object):
    name = 'mirror_processor'
    names = ['Amelia Bloom',
             'Don DeClair',
             'Lily Jordan',
             'Bo Rakenfold']
    max_names = 10

    def user_name(self, user_id):
        user = get_user(user_id)
        name = user['name']
        names = name.split(' ')
        return names[0], names[-1]

    def check_names(self, names, lastname):
        """
        Check if it's an email address or self
        """
        good_names = set()
        for name in names:
            email = re.search('@', name)
            me = re.search(lastname, name)
            if email or me:
                continue
            else:
                good_names.update(name)
        return list(good_names)

    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares
        TODO: For next show, add calendar events, subreddits, etc.
        """
        print("Processing user: ", user_data.userid)
        userid = user_data.userid
        first, last = self.user_name(userid)

        mirror_data = {}
        mirror_data['name'] = ' '.join([first, last])
        mirror_data['friends'] = []
        if 'gtext' in user_data:
            gpeople = itertools.chain.from_iterable(
                user_data['gtext']['people'])
            cleaned = self.check_names(gpeople)
            mirror_data['friends'].append(cleaned)
        else:
            mirror_data['friends'] = self.names

        if len(mirror_data['friends']) > self.max_names:
            randos = []
            for i in range(10):
                choice = random.choice(mirror_data['friends'])
                randos.append(choice)
            mirror_data['friends'] = randos

        mirror_data['work'] = []
        if 'fbprofile' in user_data:
            profile = user_data['fbprofile']
            if 'work' in profile:
                for employ in profile['work']:
                    mirror_data['work'].append(employ['name'])
            else:
                mirror_data['work'].append("DesignCraft")

        self.save_user(mirror_data, user_data)

        print("Saved Mirror Data")

    def save_user(self, data, user_data):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/mirror/user/{}.json".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                json.dump(data, fd)
        else:
            blob_enc = user_data.encrypt_blob(data)
            filename = "./data/mirror/user/{}.enc".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user(self, user):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/mirror/user/{}.json".format(user.userid)
            with open(filename, 'rb') as fd:
                return json.load(fd)
        else:
            filename = "./data/mirror/user/{}.enc".format(user.userid)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    @gen.coroutine
    def mirror_stuff(self, user, request):
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
            ('mirror', self.mirror_stuff),
        ]
