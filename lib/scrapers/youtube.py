from tornado import gen

import httplib2
from lib.config import CONFIG
from .utils import apiclient_paginate

from apiclient.discovery import build
from oauth2client import client


class YouTubeScraper(object):
    name = 'youtube'

    @gen.coroutine
    def scrape(self, user_data):
        print("Scraping user: ", user_data.userid)
        try:
            oauth = user_data.services['google']
        except KeyError:
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
        youtube = build('youtube', 'v3', http)

        userinfo = list(apiclient_paginate(youtube.channels(), 'list', {
            'part': 'statistics,contentDetails',
            'mine': True,
        }))[0]

        special_videos = {}
        user_special_playlists = userinfo['contentDetails']['relatedPlaylists']
        for name, playlistid in user_special_playlists.items():
            videos = list(apiclient_paginate(youtube.playlistItems(), 'list', {
                'part': 'snippet',
                'playlistId': playlistid,
            }))
            special_videos[name] = videos
            print(name, len(videos))

        playlists = list(apiclient_paginate(youtube.playlists(), 'list', {
            'part': 'id,snippet',
            'mine': True,
        }))
        for playlist in playlists:
            snippet = playlist['snippet']
            print(snippet['title'], snippet['description'])

        subscriptions = list(apiclient_paginate(
            youtube.subscriptions(), 'list', {
                'part': 'snippet',
                'mine': True,
            })
        )
        for subscription in subscriptions:
            snippet = subscription['snippet']
            print(snippet['title'])

        result = {
            'subscriptions': subscriptions,
            'playlists': playlists,
            'userinfo': userinfo,
            'special_videos': special_videos,
        }
        return result
