from tornado import gen
from facebook import GraphAPI

from lib.config import CONFIG
from .lib.utils import facebook_paginate
from .lib.basescraper import BaseScraper


class FBEventsScraper(BaseScraper):
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
        events = yield facebook_paginate(
            graph.get_connections('me', connection_name='events'),
            max_results=self.num_events_per_user)

        data = {"events": []}
        for item in events:
            event = {}
            event['description'] = item.get('description', None)
            event['name'] = item.get('name', None)
            event['status'] = item.get('rsvp_status', None)
            data['events'].append(event)
        return data
