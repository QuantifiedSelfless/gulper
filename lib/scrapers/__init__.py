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
    FBPhotosScraper(),
    GMailScraper(),
    FBTextScraper(),
    FBLikesScraper(),
    FBEventsScraper(),
    FBProfileScraper(),
    RedditScraper(),
    TwitterScraper()
    # GPhotosScraper(), # not being used
    # YouTubeScraper(), # not being used
    # TumblrScraper(), # not being used
    # SpotifyScraper(), # not being used
]


@gen.coroutine
def scrape(user_data):
    data = {}
    for s in scrapers:
        try:
            data[s.name] = yield s.scrape(user_data)
        except Exception as e:
            data[s.name] = None
            print("[{}] Scraper {} gave exception: {}".format(user_data.userid, s.name, e))
            traceback.print_exc()
    return data
