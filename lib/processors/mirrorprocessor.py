from tornado import gen
from .utils import process_api_handler
from .lib.db import get_user

import re
import itertools
import random


class MirrorProcessor(object):
    name = 'mirror_processor'
    data = {}
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
        good_names = []
        for name in names:
            email = re.search('@', name)
            me = re.search(lastname, name)
            if email or me:
                continue
            else:
                good_names.append(name)
        return good_names

    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares
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

        return True

    @gen.coroutine
    def mirror_stuff(self, userid, request, private_key=None):
        """
        Returns relevant data that the exhibits may want to know
        """
        return self.data.get(userid, 'userid not found')

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('mirror', self.mirror_stuff),
        ]