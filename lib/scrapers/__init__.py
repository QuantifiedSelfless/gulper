from tornado import gen

from .fbphotos import FBPhotosScraper
from .gmailscrape import GMailScraper
from .fbtext import FBTextScraper
from .fblikes import FBLikesScraper
from .fbevents import FBEventsScraper
from .fbprofile import FBProfileScraper
from .redditscrape import RedditScraper
from .twitter import TwitterScraper
# from .spotifyscrape import SpotifyScraper
# from .youtube import YouTubeScraper
# from .gphotos import GPhotosScraper
# from .tumblrscrape import TumblrScraper


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
def _scrape(s, user_data):
    try:
        s.logger.info("Starting to scrape: " + user_data.userid)
        result = yield s.scrape(user_data)
        if not result:
            s.logger.info("Scraped no data: " + user_data.userid)
        else:
            s.logger.info("Scraped data sucessfully: " + user_data.userid)
    except Exception:
        result = None
        s.logger.exception("Scraper failed on user: " + user_data.userid)
    return result


@gen.coroutine
def scrape(user_data):
    data = yield {s.name: _scrape(s, user_data) for s in scrapers}
    return data
