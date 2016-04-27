from tornado import gen

from . import scrapers
from . import processors


@gen.coroutine
def userprocess(user, use_cache=True):
    if use_cache:
        try:
            user.data = processors.DebugProcessor().load_scrape(user)
        except IOError:
            pass
    if not user.data:
        user.data = yield scrapers.scrape(user)
    user.process_results = yield processors.process(user)
