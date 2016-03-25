from tornado import gen
from tornado.httpclient import HTTPError

import httplib2
import base64
import email
from lib.config import CONFIG

from apiclient.discovery import build
from oauth2client import client

class GMailScraper(object):
    name = 'gtext'

    def paginate_messages(self, service, response):
        threads = set()
        if 'messages' in response:
            for i in response['messages']:
                threads.add(i['threadId'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId='me',
                    pageToken=page_token).execute()
            for i in response['messages']:
                threads.add(i['threadId'])
        return messages

    def get_recipient(self, email_data):
        headers = email_data['payload']['headers']
        to_field = [d['value'] for d in headers if d['name'] == 'To']
        name = to_field[0].split(' <')[0]
        return name

    def get_raw_from_id(self, service, email_id):
        try:
            msg = service.users().messages().get(userId='me', id=email_id, format='raw').execute()
            msg_str = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
            mime_msg = email.message_from_string(msg_str)
            text = mime_msg.get_payload()[0]
            return text
        except HTTPError as e:
            print("Exception while scraping gmail: ", e)


    def get_meta_from_id(self, service, email_id):
        try:
            meta = service.users().messages().get(userId='me', id=email_id, format='metadata').execute()
            return meta
        except HTTPError as e:
            print("Exception while scraping gmail: ", e)

    def get_beg_thread(self, service, thread_id):
        try:
            thr = service.users().threads().get(userId='me', id=thread_id).execute()
            firstm = thr['messages'][0]['id']
            return self.get_raw_from_id(firstm)
        except HTTPError as e:
            print("Exception while scraping gmail: ", e)


    @gen.coroutine
    def scrape(self, user_data):
        """
        Scrapes text and contacts from user gmail account
            https://developers.google.com/gmail/api/v1/reference/
        """

        try:
            oauth = user_data.services['google']
        except KeyError:
            return False
        if 'denied' in oauth:
            return False

        creds = client.OAuth2Credentials(
            access_token=oauth['access_token'],
            client_id=CONFIG.get('google_client_id'),
            client_secret=CONFIG.get('google_client_secret'),
            refresh_token=oauth.get('refresh_token', None),
            token_uri=client.GOOGLE_TOKEN_URI,
            token_expiry=oauth.get('expires_in', None),
            user_agent='QS-server-agent/1.0',
            id_token=oauth.get('id_token', None)
        )

        data = {
            "text" : [],
            "people" : set(),
            "snippets" : []
        }

        #Set up client
        http = creds.authorize(httplib2.Http())
        gmail = build('gmail', 'v1', http=http)
        print("[gmail] Scraping user: ", user_data.userid)

        #Get seed language tokens
        with open('snippets.txt', 'r') as fd:
            tokens = [s.strip() for s in fd]

        #Go through each token, seed a search
        while tokens:
            next_q = tokens.pop()
            res = gmail.users().messages().list(userId='me', q='in:sent {0}'.format(next_q)).execute()
            threads = 

        return data
        