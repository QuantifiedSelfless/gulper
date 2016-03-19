from tornado import gen

import httplib2
from lib.config import CONFIG
from .utils import apiclient_paginate

from apiclient.discovery import build
from oauth2client import client


class GPhotosScraper(object):
    name = 'gphotos'

    @gen.coroutine
    def scrape(self, user_data):
        """
        Scrape photos from google photos using the following API:
            https://developers.google.com/picasa-web/docs/2.0/developers_guide_protocol
        """
        print("Scraping user: ", user_data.userid)
        try:
            oauth = user_data.services['google']
        except KeyError:
            return False
        if oauth in ('noshare', 'noacct'):
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
        gphotos = build('picassa', 'v3', http)

        result = {}
        return result
