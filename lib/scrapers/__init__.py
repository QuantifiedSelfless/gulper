from tornado import gen

from .samplescraper import SampleScraper
from .youtube import YouTubeScraper
from .gphotos import GPhotosScraper
from .fbphotos import FBPhotosScraper

import traceback


scrapers = [
    SampleScraper(),
    YouTubeScraper(),
    GPhotosScraper(),
    FBPhotosScraper(),
]


@gen.coroutine
def scrape(user_data):
    data = {}
    for s in scrapers:
        try:
            data[s.name] = yield s.scrape(user_data)
        except Exception as e:
            data[s.name] = None
            print("Scraper {} gave exception: {}".format(s.name, e))
            traceback.print_exc()
    return data
