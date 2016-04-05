from tornado import gen
import tweepy

from ..config import CONFIG


class TwitterScraper(object):
    name = 'twitter'

    @property
    def num_scrape(self):
        if CONFIG['_mode'] == 'prod':
            return 1000
        return 100

    @gen.coroutine
    def all_following(self, api, follow_list):
        data = []
        count = 0
        for follow in follow_list:
            if count > self.num_scrape:
                break
            user = {}
            nextone = api.get_user(follow)
            user['name'] = nextone.name
            user['description'] = nextone.description
            data.append(user)
            count += 1

        return data

    @gen.coroutine
    def all_favs(self, api, favs):
        data = []
        count = 0
        res = favs
        while count < self.num_scrape and len(res) > 0:
            for fav in res:
                data.append(fav.text)
                count += 1
            max_id = res.max_id
            res = api.favorites(max_id=max_id)
        return data

    @gen.coroutine
    def all_tweets(self, api, total, tweets):
        data = []
        count = 0
        res = tweets
        while len(data) < total and count < self.num_scrape and len(res) > 0:
            for tweet in res:
                data.append(tweet.text)
                count += 1
            max_id = res.max_id
            res = api.user_timeline(max_id=max_id)
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

        auth = tweepy.OAuthHandler(
            CONFIG.get('twitter_client_key'),
            CONFIG.get('twitter_client_secret')
        )
        auth.secure = True
        auth.set_access_token(
            # these dictionary keys may be wrong
            twitter_creds['access_token'],
            twitter_creds['access_token_secret']
        )
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
        data["following"] = self.all_following(api, following)

        favs = api.favorites()
        data['favorites'] = self.all_favs(api, favs)

        tweets = api.user_timeline()
        data['tweets'] = self.all_tweets(api, me.statuses_count, tweets)

        return data
