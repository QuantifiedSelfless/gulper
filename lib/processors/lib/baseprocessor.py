import logging
import pickle
import os

from ...config import CONFIG


FORMAT = '[%(levelname)1.1s %(asctime)s %(name)s:%(lineno)d] %(message)s'


class BaseProcessor(object):
    def __init__(self, *args, **kwargs):
        logging.basicConfig(format=FORMAT)
        self.logger = logging.getLogger("processor." + self.name)

    def save_user_blob(self, blob, user):
        filedata = dict(name=self.name, uid=user.userid)
        os.makedirs("./data/{name}/user".format(**filedata), exist_ok=True)
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/{name}/user/{uid}.pkl".format(**filedata)
            with open(filename, 'wb+') as fd:
                pickle.dump(blob, fd)
        else:
            blob_enc = user.encrypt_blob(blob)
            filename = "./data/{name}/user/{uid}.enc".format(**filedata)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user_blob(self, user):
        filedata = dict(name=self.name, uid=user.userid)
        try:
            filename = "./data/{name}/user/{uid}.pkl".format(**filedata)
            with open(filename, 'rb') as fd:
                return pickle.load(fd)
        except IOError:
            filename = "./data/{name}/user/{uid}.enc".format(**filedata)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    def load_keywords(self, datafile):
        filename = './lib/processors/data/' + datafile
        try:
            with open(filename) as fd:
                return [kw.strip() for kw in fd]
        except IOError:
            self.logger.exception("Could not load keywords: " + filename)
