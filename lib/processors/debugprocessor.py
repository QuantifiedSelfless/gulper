from tornado import gen
import pickle
import os

from ..config import CONFIG
from .lib.baseprocessor import BaseProcessor


class DebugProcessor(BaseProcessor):
    name = 'debug_processor'

    @gen.coroutine
    def process(self, user_data):
        """
        Save user data for inspection
        """
        if CONFIG.get('_mode') != 'dev':
            return False
        filename = "./data/debug/{}.pkl".format(user_data.userid)
        os.makedirs('./data/debug', exist_ok=True)
        with open(filename, 'wb+') as fd:
            pickle.dump(user_data.data, fd)
        self.logger.info("Saved user {} to {}".format(user_data.userid,
                                                      filename))
        return True
