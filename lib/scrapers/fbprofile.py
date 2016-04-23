from tornado import gen
from facebook import GraphAPI

from .lib.basescraper import BaseScraper


class FBProfileScraper(BaseScraper):
    name = 'fbprofile'

    @gen.coroutine
    def scrape(self, user_data):
        try:
            oauth = user_data.services['facebook']['access_token']
        except KeyError:
            return False
        graph = GraphAPI(access_token=oauth)
        profile = graph.get_object(
            'me',
            fields='bio, birthday,education,interested_in,hometown,'
                   'political,relationship_status, religion, work'
        )
        data = profile
        return data
