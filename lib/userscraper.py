from tornado import gen
import cryptohelper
import pickle

from . import scrapers
from . import processors
from .config import CONFIG


class UserScraper(object):
    def __init__(self, userid, publickey_pem, services):
        self.userid = userid
        self.services = services
        self.publickey_pem = publickey_pem
        if publickey_pem is not None:
            self.publickey = cryptohelper.import_key(publickey_pem)
        else:
            self.publickey = None
        self.data = {}

    @gen.coroutine
    def start(self):
        if CONFIG.get('_mode') == 'dev':
            try:
                fname = './data/debug/{}.pkl'.format(self.userid)
                with open(fname, 'rb') as fd:
                    self.data = pickle.load(fd)
                print("Found debug data for user: ", self.userid)
            except IOError:
                pass
        if not self.data:
            self.data = yield scrapers.scrape(self)
        self.process_results = yield processors.process(self)

    def _save_process_results(self, results):
        #  TODO: should this ping back to QS or save in it's own DB?
        pass

    def encrypt_blob(self, data):
        return cryptohelper.encrypt_blob(self.publickey, data)
