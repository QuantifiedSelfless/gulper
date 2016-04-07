from tornado import gen

from .samplescraper import SampleScraper
from .youtube import YouTubeScraper
from .gphotos import GPhotosScraper
from .fbphotos import FBPhotosScraper
from .gmailscrape import GMailScraper
from .fbtext import FBTextScraper
from .fblikes import FBLikesScraper
from .fbevents import FBEventsScraper
from .fbprofile import FBProfileScraper
from .tumblrscrape import TumblrScraper
from .spotifyscrape import SpotifyScraper
from .redditscrape import RedditScraper
from .twitter import TwitterScraper
import os
import ujson as json

scrapers = [
#    SampleScraper(),
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
    for scraper in scrapers:
        try:
            data[scraper.name] = yield scraper.scrape(user_data)
            with open('data/{0}-{1}'.format(user_data.userid, scraper.name), 'w+') as fd:
                json.dump(data[scraper.name], fd)
        except Exception as ex:
            print("Scraper '{0}' failed to populate data for user with id {1}".format(scraper.name, user_data.userid))
            print(ex)
            data[scraper.name] = False
    return data
