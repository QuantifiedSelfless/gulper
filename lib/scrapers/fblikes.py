from tornado import gen

from facebook import GraphAPI
from .utils import facebook_paginate

class FBLikesScraper(object):
    name = 'fblikes'

    @property
    def num_likes_per_user(self):
        if CONFIG['_mode'] == 'prod':
            return 1000
        return 100

    @gen.coroutine
    def scrape(self, user_data):
        try:
            oauth = user_data.services['facebook']['access_token']
        except KeyError:
            return False
        graph = GraphAPI(access_token=oauth)
        print("[fbprofile] Scraping user: ", user_data.userid)

        likes = facebook_paginate(
            graph.get_connections('me', connection_name='likes'),
            max_results=self.num_likes_per_user)

        data = { 'likes' : [] }

        for like in likes:
            data['likes'].append(like['name'])

        return data

if __name__ == '__main__':
    import sys
    import json
    myFile = sys.argv[1]
    fd = open(myFile, 'r')
    data = fd.read()
    fd.close()
    tokens = json.loads(data)
    FBLikesScraper()
    
    print(FBLikesScraper.scrape())



    