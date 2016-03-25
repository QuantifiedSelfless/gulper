from tornado import gen

from .samplescraper import SampleScraper
from .youtube import YouTubeScraper
from .gphotos import GPhotosScraper
from .fbphotos import FBPhotosScraper
from .gmailscrape import GMailScraper


scrapers = [
    SampleScraper(),
    YouTubeScraper(),
    GPhotosScraper(),
    FBPhotosScraper(),
    GMailScraper()
]


@gen.coroutine
def scrape(user_data):
    data = yield {s.name: s.scrape(user_data) for s in scrapers}
    return data
