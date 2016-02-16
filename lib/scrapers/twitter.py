from tornado import gen
import tweepy

from ..config import CONFIG


class SampleScraper(object):
    @gen.coroutine
    def scrape(self, user_data):
        print("Scraping user: ", user_data.userid)
        auth = tweepy.OAuthHandler(
            CONFIG.get('twitter_client_key'),
            CONFIG.get('twitter_client_secret')
        )
        auth.secure = True
        twitter_creds = user_data.services['twitter']
        auth.set_access_token(
            # these dictionary keys may be wrong
            twitter_creds['access_token'],
            twitter_creds['access_token_secret']
        )
        api = tweepy.API(auth)
        print(api)
