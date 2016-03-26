from tornado import gen

from facebook import GraphAPI
from lib.config import CONFIG
from .utils import facebook_paginate

class FBTextScraper(object):
    name = 'fbtext'

    @property
    def num_posts_per_user(self):
        if CONFIG['_mode'] == 'prod':
            return 2000
        return 100

    def message_filter(self, data):
        pfiltered = []
        lfiltered =[]
        for i in data:
            if 'message' in i:
                pfiltered.append(i['message'])
            if 'link' in i:
                lfiltered.append(i['link'])
        return pfiltered, lfiltered



    @gen.coroutine
    def scrape(self, user_data):
        try:
            oauth = user_data.services['facebook']['access_token']
        except KeyError:
            return False
        graph = GraphAPI(access_token=oauth)
        print("[fbtext] Scraping user: ", user_data.userid)
        data = {
            "text": [],
            "links": []
        }

        posts = []
        while len(posts) < self.num_posts_per_user:
            posts_blob = yield facebook_paginate(
                graph.get_connections(
                    'me',
                    'posts',
                    fields='message, link'
                ),
                max_results=self.num_posts_per_user
            )
            posts, links = self.message_filter(posts_blob)

        #To do comments we'd have to go through the different posts and look
        #Scraping the person's feed is another option, but we get more garbage that way

        data['text'] = posts
        data['links'] = links
        return data