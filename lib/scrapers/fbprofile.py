from tornado import gen

from facebook import GraphAPI

class FBProfileScraper(object):
    name = 'fbprofile'

    @gen.coroutine
    def scrape(self, user_data):
        try:
            oauth = user_data.services['facebook']['access_token']
        except KeyError:
            return False
        graph = GraphAPI(access_token=oauth)
        print("[fbprofile] Scraping user: ", user_data.userid)

        profile = graph.get_object('me', 
            fields = 'bio, birthday, education, interested_in, hometown, political, relationship_status, religion, work')

        data = profile
        return data
