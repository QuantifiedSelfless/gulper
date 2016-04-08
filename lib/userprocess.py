from tornado import gen
import pickle

from . import scrapers
from . import processors
from .config import CONFIG


@gen.coroutine
def userprocess(user):
    if CONFIG.get('_mode') == 'dev':
        try:
            fname = './data/debug/{}.pkl'.format(user.userid)
            with open(fname, 'rb') as fd:
                user.data = pickle.load(fd)
            print("Found debug data for user: ", user.userid)
        except IOError:
            pass
    if not user.data:
        user.data = yield scrapers.scrape(user)
    user.process_results = yield processors.process(user)
