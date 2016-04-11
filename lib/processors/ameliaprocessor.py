from tornado import gen
from .lib.utils import process_api_handler
from ..config import CONFIG
from .lib.baseprocessor import BaseProcessor

import ujson as json
import random
import os


class AmeliaProcessor(BaseProcessor):
    name = 'amelia_processor'

    def __init__(self):
        super().__init__()
        if not os.path.exists("./data/amelia"):
            os.makedirs("./data/amelia")
        try:
            fname = './data/amelia/backend.json'
            with open(fname, 'rb') as fd:
                self.names = json.load(fd)
            self.logger.info("Loaded backend from save state")
        except (IOError, ValueError):
            self.logger.info("No names yet")
            self.names = {"ids": []}

    @gen.coroutine
    def process(self, user_data):
        if user_data.data.get('fbprofile'):
            person = user_data.data['fbprofile']['id']
            if user_data.data['fbprofile'].get('work'):
                if user_data.data['fbprofile'].get('hometown'):
                    if user_data.data['fbprofile'].get('education'):
                        self.names['ids'].append(person)
                        self.save_names(self.names, user_data)
                        return True
        return False

    def save_names(self, data, user_data):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/amelia/backend.json".format(user_data.userid)
            with open(filename, 'w+') as fd:
                json.dump(data, fd)
        else:
            blob_enc = user_data.encrypt_blob(data)
            filename = "./data/amelia/backend.enc".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_names(self, user):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/amelia/backend.json".format(user.userid)
            with open(filename, 'r') as fd:
                return json.load(fd)
        else:
            filename = "./data/amelia/backend.enc".format(user.userid)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    @gen.coroutine
    def get_friend(self, user, request):
        """
        Returns relevant data that the exhibits may want to know
        TODO: Decide key we encrypt with and what the expected request will be
        """
        data = self.load_names(user)
        name = random.choice(data['names'])
        return name

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('ameliafriend', self.get_friend),
        ]
