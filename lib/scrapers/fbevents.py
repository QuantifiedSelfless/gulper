from tornado import gen
from facebook import GraphAPI
from .utils import facebook_paginate
from lib.config import CONFIG


class FBEventsScraper(object):
    name = 'fbevents'

    @property
    def num_events_per_user(self):
        if CONFIG['_mode'] == 'prod':
            return 100
        return 10

    @gen.coroutine
    def scrape(self, user_data):
        try:
            oauth = user_data.services['facebook']['access_token']
        except KeyError:
            return False
        graph = GraphAPI(access_token=oauth)
        print("[fbevents] Scraping user: ", user_data.userid)

        events = yield facebook_paginate(
            graph.get_connections('me', connection_name='events'),
            max_results=self.num_events_per_user)

        data = {"events": []}

        for thing in events:
            eve = {}
            eve['description'] = thing.get('description', None)
            eve['name'] = thing.get('name', None)
            eve['status'] = thing.get('rsvp_status', None)
            data['events'].append(eve)
        return data
