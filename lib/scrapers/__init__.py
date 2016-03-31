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
    data = yield {s.name: s.scrape(user_data) for s in scrapers}
    #DELETE THIS LATER
    print(data)
    return data
