from tornado import gen

from . import scrapers
from . import processors


@gen.coroutine
def userprocess(users, use_cache=True):
    for user in users:
        if use_cache:
            try:
                user.data = processors.DebugProcessor().load_scrape(user)
            except IOError:
                pass
        if not user.data:
            user.data = yield scrapers.scrape(user)
        user.process_results = yield processors.process(user)
