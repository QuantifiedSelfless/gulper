import praw
from tornado import gen
from lib.config import CONFIG


class RedditScraper(object):
    name = 'reddit'

    @property
    def num_scrape(self):
        if CONFIG['_mode'] == 'prod':
            return 1000
        return 100

    @gen.coroutine
    def scrape(self, user_data):
        try:
            tokens = user_data.services['reddit']
        except KeyError:
            return False
        if 'denied' in tokens:
            return False
        client_id = CONFIG.get("reddit_client_id")
        client_secret = CONFIG.get("reddit_client_secret")

        r = praw.Reddit(user_agent="QS-agent/1.0")
        r.set_oauth_app_info(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://iamadatapoint.com:8085/auth/reddit")
        tokens = r.refresh_access_information(
            refresh_token=tokens['refresh_token'])
        r.set_access_credentials(**tokens)

        data = {}

        subs = []
        count = 0
        for i in r.get_my_subreddits():
            if count > self.num_scrape:
                break
            load = {}
            load['name'] = i.display_name
            load['url'] = i.url
            subs.append(load)
            count += 1

        data['subs'] = subs

        msgs = []
        count = 0
        for i in r.get_inbox():
            if count > self.num_scrape:
                break
            print(i)
            load = {}
            load['body'] = i.body
            if i.author:
                load['author'] = i.author.name
            load['comment'] = i.was_comment
            msgs.append(load)
            count += 1

        data['text'] = msgs

        me = r.get_me()
        karma_c = me.comment_karma
        karma_l = me.link_karma

        submissions = []
        count = 0
        for i in me.get_submitted():
            if count > self.num_scrape:
                break
            load = {}
            load['title'] = i.title
            load['url'] = i.url
            load['score'] = i.score
            load['subreddit'] = i.subreddit.title
            submissions.append(load)
            count += 1

        data['submissions'] = submissions

        data['comment_karma'] = karma_c
        data['link_karma'] = karma_l

        likes = []
        count = 0
        for i in me.get_upvoted():
            if count > self.num_scrape:
                break
            load = {}
            load['title'] = i.title
            load['url'] = i.url
            likes.append(load)
            count += 1

        data['likes'] = likes

        dislikes = []
        count = 0
        for i in me.get_downvoted():
            if count > self.num_scrape:
                break
            load = {}
            load['title'] = i.title
            load['url'] = i.url
            dislikes.append(load)
            count += 1

        data['dislikes'] = dislikes
        return data
