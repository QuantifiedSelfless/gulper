from tornado import gen
import logging
import cryptohelper

from . import scrapers
from . import processors


class UserScraper(object):
    def __init__(self, userid, publickey_pem, services):
        self.userid = userid
        self.publickey_pem = publickey_pem
        self.publickey = cryptohelper.import_key(publickey_pem)
        self.services = services
        self.data = {}

    def start(self):
        self.data = yield scrapers.scrape(self)
        self.process_results = processors.process(self)

    @gen.coroutine
    def _wrap_scrape(self, scraper):
        try:
            data = yield scraper(self.userid, self.services)
            self.data.update(data)
            return True
        except Exception:
            logging.exception("Could not run scaper")
            return False
