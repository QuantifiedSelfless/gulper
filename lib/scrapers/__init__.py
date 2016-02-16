from tornado import gen

from .samplescraper import SampleScraper
from .youtube import YouTubeScraper


scrapers = [
    SampleScraper(),
    YouTubeScraper()
]


@gen.coroutine
def scrape(user_data):
    data = yield {s.name: s.scrape(user_data) for s in scrapers}
    return data
