from tornado import gen
from .lib.handler import process_api_handler
from .lib.baseprocessor import BaseProcessor

from collections import defaultdict
import ujson as json
import os


class AmeliaProcessor(BaseProcessor):
    name = 'amelia_processor'

    def __init__(self):
        super().__init__()

    @gen.coroutine
    def process(self, user_data):
        if user_data.data.get('fbprofile'):
            if user_data.data['fbprofile'].get('work'):
                if user_data.data['fbprofile'].get('hometown'):
                    if user_data.data['fbprofile'].get('education'):
                        self.save_name(user_data)
                        self.logger.info("Successfully processed amelia data for User %s" % user_data.userid)
                        return True
        return False

    def save_name(self, user_data):
        data = {
            "fbid": user_data.data['fbprofile']['id'],
            "showid": user_data.meta['showid'],
            "showdate": user_data.meta['showdate'],
        }
        os.makedirs("./data/" + self.name, exist_ok=True)
        filename = "./data/{}/{}.json".format(self.name, user_data.userid)
        with open(filename, "w+") as fd:
            json.dump(data, fd)

    def delete_data(self, user_data):
        filename = "./data/{}/{}.json".format(self.name, user_data.userid)
        try:
            os.remove(filename)
            return True
        except FileNotFoundError:
            return False

    @gen.coroutine
    def get_friend(self, user, request):
        """
        Returns relevant data that the exhibits may want to know
        """
        result = defaultdict(list)
        data_root = "./data/{}/".format(self.name)
        for filename in os.listdir(data_root):
            if not filename.endswith('.json'):
                continue
            with open(data_root + filename) as fd:
                data = json.load(fd)
                result[data['showid']].append(data)
        return list(result.values())

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('ameliafriend', self.get_friend),
        ]
