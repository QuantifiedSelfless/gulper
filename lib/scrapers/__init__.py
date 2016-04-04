from tornado import gen

from .samplescraper import SampleScraper
from .youtube import YouTubeScraper
from .gphotos import GPhotosScraper
from .fbphotos import FBPhotosScraper
from .gmailscrape import GMailScraper
from .fbtext import FBTextScraper
from .fblikes import FBLikesScraper
from .fbevents import FBEventsScraper
from .tumblrscrape import TumblrScraper
from .spotifyscrape import SpotifyScraper
from .redditscrape import RedditScraper


scrapers = [
    SampleScraper(),
    YouTubeScraper(),
    GPhotosScraper(),
    FBPhotosScraper(),
    GMailScraper(),
    FBTextScraper(),
    FBLikesScraper(),
    FBEventsScraper(),
    TumblrScraper(),
    RedditScraper(),
    SpotifyScraper()
]


@gen.coroutine
def scrape(user_data):
    data = {}
    for scraper in scrapers:
        try:
            data[scraper.name] = yield scraper.scrape(user_data)
        except Exception as ex:
            print("Scraper '{0}' failed to populate data for user with id {1}".format(scraper.name, user_data.userid))
            print(ex)
            continue
    #DELETE THIS LATER
    print(data)
    return data
