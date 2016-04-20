from tornado import gen
import tweepy

from ..config import CONFIG


class TwitterScraper(object):
    name = 'twitter'

    @property
    def tweet_scrape(self):
        if CONFIG['_mode'] == 'prod':
            return 250
        return 10

    @property
    def follow_scrape(self):
        if CONFIG['_mode'] == 'prod':
            return 75
        return 10

    @gen.coroutine
    def all_following(self, api, follow_list):
        data = []
        count = 0
        for follow in follow_list:
            if count > self.follow_scrape:
                break
            user = {}
            for _ in range(3):
                try:
                    nextone = api.get_user(follow)
                    break
                except tweepy.RateLimitError:
                    yield gen.sleep(5 * 60)
            else:
                continue

            user['name'] = nextone.name
            user['description'] = nextone.description
            data.append(user)
            count += 1

        return data

    @gen.coroutine
    def all_tweets(self, api, total, tweets):
        data = []
        count = 0
        res = tweets
        while len(data) < total and count < self.tweet_scrape and len(res) > 0:
            for tweet in res:
                data.append(tweet.text)
                count += 1
            max_id = res.max_id
            for _ in range(3):
                try:
                    res = api.user_timeline(max_id=max_id)
                    break
                except tweepy.RateLimitError:
                    yield gen.sleep(5 * 60)
            else:
                continue

        return data

    @gen.coroutine
    def scrape(self, user_data):

        print("Scraping user: ", user_data.userid)
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

        data = {}

        me = api.me()
        profile_data = {
            "followers": me.followers_count,
            "description": me.description,
            "name": me.name,

        }
        data["profile"] = profile_data

        following = api.friends_ids()
        data["following"] = yield self.all_following(api, following)

        tweets = api.user_timeline()
        data['tweets'] = yield self.all_tweets(api, me.statuses_count, tweets)

        return data
