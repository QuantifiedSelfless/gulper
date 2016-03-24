from tornado import gen

import httplib2
from lib.config import CONFIG
from lib.facefinder import find_faces_url
from .utils import apiclient_paginate
import io

from apiclient.discovery import build
from apiclient.http import MediaIoBaseDownload
from oauth2client import client


def gdrive_get_file(drive, file_id):
    request = drive.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download {}%%.".format(int(status.progress() * 100)))
    return fh


class GPhotosScraper(object):
    name = 'gphotos'

    @property
    def num_images_per_user(self):
        if CONFIG['_mode'] == 'prod':
            return 1000
        return 100

    @gen.coroutine
    def scrape(self, user_data):
        """
        Scrape photos from google photos using the following API:
            https://developers.google.com/drive/v3/reference/
        """
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
        gplus = build('drive', 'v3', http)
        print("[gphotos] Scraping user: ", user_data.userid)

        photos = list(apiclient_paginate(gplus.files(), 'list', {
            'spaces': 'photos',
            'fields': 'files,kind,nextPageToken',
        }, max_results=self.num_images_per_user))
        for photo in photos:
            faces = yield find_faces_url(photo['thumbnailLink'], upsample=2)
            photo['faces'] = faces

        return photos
