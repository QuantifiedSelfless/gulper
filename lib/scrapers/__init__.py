from tornado import gen

from .youtube import YouTubeScraper
from .gphotos import GPhotosScraper
from .fbphotos import FBPhotosScraper
from .gmailscrape import GMailScraper
from .fbtext import FBTextScraper
from .fblikes import FBLikesScraper
from .fbevents import FBEventsScraper
from .fbprofile import FBProfileScraper
from .tumblrscrape import TumblrScraper
from .redditscrape import RedditScraper
from .spotifyscrape import SpotifyScraper
from .twitter import TwitterScraper

import traceback


scrapers = [
    YouTubeScraper(),
    GPhotosScraper(),
    FBPhotosScraper(),
    GMailScraper(),
    FBTextScraper(),
    FBLikesScraper(),
    FBEventsScraper(),
    FBProfileScraper(),
    TumblrScraper(),
    RedditScraper(),
    SpotifyScraper(),
    TwitterScraper()
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
