from tornado import gen

import httplib2
from lib.config import CONFIG
from .utils import apiclient_paginate

from apiclient.discovery import build
from oauth2client import client


class YouTubeScraper(object):
    name = 'youtube'

    @property
    def num_videos_per_playlist(self):
        if CONFIG['_mode'] == 'prod':
            return 250
        return 25

    @gen.coroutine
    def scrape(self, user_data):
        try:
            oauth = user_data.services['google']
        except KeyError:
            return False
        if 'denied' in oauth:
            return False
        credentials = client.OAuth2Credentials(
            access_token=oauth['access_token'],
            client_id=CONFIG.get('google_client_id'),
            client_secret=CONFIG.get('google_client_secret'),
            refresh_token=oauth.get('refresh_token', None),
            token_uri=client.GOOGLE_TOKEN_URI,
            token_expiry=oauth.get('expires_in', None),
            user_agent='QS-server-agent/1.0',
            id_token=oauth.get('id_token', None)
        )
        http = credentials.authorize(httplib2.Http())
        try:
            youtube = build('youtube', 'v3', http=http)
        except:
            print("This user's account doesn't have youtube")

        print("[youtube] Scraping user: ", user_data.userid)

        userinfo = list(apiclient_paginate(youtube.channels(), 'list', {
            'part': 'statistics,contentDetails',
            'mine': True,
        }))[0]

        special_videos = {}
        user_special_playlists = userinfo['contentDetails']['relatedPlaylists']
        for name, playlistid in user_special_playlists.items():
            try:
                videos = list(
                    apiclient_paginate(youtube.playlistItems(),
                    'list',
                    {
                        'part': 'snippet',
                        'playlistId': playlistid,
                    }, max_results=self.num_videos_per_playlist))
                special_videos[name] = videos
            except Exception as e:
                print("Error fetching from Youtube API: {0}".format(e))
                continue

        playlists = list(apiclient_paginate(youtube.playlists(), 'list', {
            'part': 'id,snippet',
            'mine': True,
        }))

        subscriptions = list(apiclient_paginate(
            youtube.subscriptions(), 'list', {
                'part': 'snippet',
                'mine': True,
            })
        )

        result = {
            'subscriptions': subscriptions,
            'playlists': playlists,
            'userinfo': userinfo,
            'special_videos': special_videos,
        }
        return result
