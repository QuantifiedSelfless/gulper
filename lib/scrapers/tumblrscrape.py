from tornado import gen

import pytumblr
from lib.config import CONFIG


class TumblrScraper(object):

    name = 'tumblr'

    @property
    def num_likes(self):
        if CONFIG['_mode'] == 'prod':
            return 1000
        return 100

    @gen.coroutine
    def paginate_likes(self, client, count):
        data = []
        maxresults = self.num_likes
        x = 20
        while x < maxresults and x < count:
            try:
                req = client.likes(offset=x)
                data.append(req['liked_posts'])
            except KeyError as e:
                print("Exception requesting tumblr likes: ", e)
                break
            x += 20
        return data

    def clean_likes(self, data):
        cleaned = []

        for i in data:
            goods = {}
            goods['source_title'] = data.get('source_title', None)
            goods['post_url'] = data.get('post_url', None)
            goods['date'] = data.get('date', None)
            goods['summary'] = data.get('summary', None)
            goods['photos'] = data.get('photos', None)
            goods['blog_name'] = data.get('blog_name', None)
            goods['content'] = data.get('content', None)

            cleaned.append(goods)

        return cleaned

    @gen.coroutine
    def scrape(self, user_data):
        try:
            access = user_data.services['tumblr']['access_token']
            secret = user_data.services['tumblr']['access_token_secret']
        except KeyError:
            return False

        if 'denied' in access:
            return False

        consumer_key = CONFIG.get("tumblr_client_id")
        consumer_secret = CONFIG.get("tumblr_client_secret")
        client = pytumblr(access, secret, consumer_key, consumer_secret)

        tumblr_data = {
            "hosted_blogs": [],
            "following": [],
            "likes": [],
            "suggestions": []
        }

        profile = client.info()
        total_likes = profile['user']['likes']
        total_following = profile['user']['following']

        #Should we be doing anything in case we get garbage/shell accounts?
        # Write this comment in GitHub
        if total_likes == 0 and total_following == 0:
            return "Empty Account"

        hosts = []
        for i in profile['user']['blogs']:
            blog = {}
            blog['total_posts'] = i['total_posts']
            blog['followers'] = i['followers']
            blog['description'] = i['description']
            blog['url'] = i['url']
            blog['name'] = i['name']
            blog['title'] = i['title']
            hosts.append(blog)

        tumblr_data['hosted_blogs'] = hosts

        dash = client.dashboard()
        dash_data = []
        for data in dash['posts']:
            goods = {}
            goods['source_title'] = data.get('source_title', None)
            goods['post_url'] = data.get('post_url', None)
            goods['date'] = data.get('date', None)
            goods['summary'] = data.get('summary', None)
            goods['photos'] = data.get('photos', None)
            goods['blog_name'] = data.get('blog_name', None)
            goods['text'] = data.get('text', None)
            goods['caption'] = data.get('caption', None)
            goods['source_url'] = data.get('source_url', None)
            goods['content'] = data.get('content', None)
            dash_data.append(goods)

        tumblr_data['suggestions'] = dash_data

        like_data = []
        likes = client.likes()
        total = likes['liked_count']
        like_data = likes['liked_posts']
        if total > 20:
            full_set = yield self.paginate_likes(client, total)
            like_data.append(full_set)

        tumblr_data['likes'] = self.clean_likes(like_data)
        follows = client.following()
        tumblr_data['follows'] = follows

        return tumblr_data
