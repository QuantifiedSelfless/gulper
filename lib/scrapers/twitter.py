from tornado import gen
import tweepy

from ..config import CONFIG
from .lib.basescraper import BaseScraper


@gen.coroutine
def ratelimit_backoff(fxn, *args, **kwargs):
    for _ in range(3):
        try:
            return fxn(*args, **kwargs)
        except tweepy.RateLimitError:
            yield gen.sleep(5 * 60)
    raise tweepy.RateLimitError()


class TwitterScraper(BaseScraper):
    name = 'twitter'

    @property
    def num_tweet_scrape(self):
        if CONFIG['_mode'] == 'prod':
            return 250
        return 10

    @property
    def num_follow_scrape(self):
        if CONFIG['_mode'] == 'prod':
            return 70
        return 10

    @gen.coroutine
    def all_following(self, api):
        data = []
        friends = yield ratelimit_backoff(api.friends_ids)
        for friend in friends:
            if len(data) > self.num_follow_scrape:
                break
            friend_meta = yield ratelimit_backoff(api.get_user, friend)
            user = {
                'name': friend_meta.name,
                'description': friend_meta.description,
            }
            data.append(user)
            yield gen.sleep(0)
        return data

    @gen.coroutine
    def all_tweets(self, api, max_tweets):
        data = []
        max_id = None
        max_tweets = max(max_tweets, self.num_tweet_scrape)
        while True:
            tweets = yield ratelimit_backoff(api.user_timeline,
                                             max_id=max_id)
            if not tweets or len(data) >= max_tweets:
                break
            data.extend(t.text for t in tweets)
            max_id = tweets.max_id
            yield gen.sleep(0)
        return data

    @gen.coroutine
    def scrape(self, user_data):
        try:
            twitter_creds = user_data.services['twitter']
        except:
            return False
        if 'denied' in twitter_creds:
            return False

        client_key = CONFIG.get('twitter_client_id')
        client_secret = CONFIG.get('twitter_client_secret')
        auth = tweepy.OAuthHandler(
                client_key,
                client_secret
        )
        auth.access_token = twitter_creds['access_token']
        auth.access_token_secret = twitter_creds['access_token_secret']
        api = tweepy.API(auth)
        me = yield ratelimit_backoff(api.me)
        profile_data = {
            "followers": me.followers_count,
            "description": me.description,
            "name": me.name,
        }
        data = {}
        data["profile"] = profile_data
        data["following"] = yield self.all_following(api)
        data['tweets'] = yield self.all_tweets(api, me.statuses_count)
        return data
