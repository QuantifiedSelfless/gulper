import logging


FORMAT = '[%(levelname)1.1s %(asctime)s %(name)s:%(lineno)d] %(message)s'


class BaseScraper(object):
    def __init__(self, *args, **kwargs):
        logging.basicConfig(format=FORMAT)
        self.logger = logging.getLogger("scraper." + self.name)
