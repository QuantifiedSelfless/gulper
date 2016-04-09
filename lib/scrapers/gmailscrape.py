from tornado import gen
from tornado.httpclient import HTTPError

import httplib2
import base64
from email.parser import BytesParser as EmailParser
from email import policy
from lib.config import CONFIG
import random

from apiclient.discovery import build
from oauth2client import client


def equalize_dict(data, max_num):
    """
    Quick and dirty code to randomly sample from a dictionary of lists in order
    to roughly equalize their lengths so that IN TOTAL we have `max_num`
    elements.
    NOTE: this will randomly shuffle the values of the data so don't expect it
    to maintain any oder
    """
    max_per_bin = max_num // len(data)
    to_kill = sum(map(len, data.values())) - max_num
    while to_kill > 0:
        for key, values in data.items():
            if len(values) <= max_per_bin:
                continue
            dv = min(to_kill, len(values) - max_per_bin)
            killing = random.randint(1, int(dv))
            random.shuffle(values)
            for i in range(killing):
                values.pop()
            to_kill -= killing
            if to_kill <= 0:
                break
    return data


class GMailScraper(object):
    name = 'gtext'

    def __init__(self):
        self.tokens = []
        with open('lib/scrapers/snippets.txt', 'r') as fd:
            self.tokens = [s.strip() for s in fd]

    @property
    def num_threads(self):
        if CONFIG['_mode'] == 'prod':
            return 1000
        return 100

    def get_content(self, raw):
        data = base64.urlsafe_b64decode(raw)
        email_parser = EmailParser(policy=policy.default)
        email = email_parser.parsebytes(data)
        plain = email.get_body(preferencelist=('plain',))
        body = None
        if plain:
            body = plain.get_payload()
        email_dict = dict(email)
        email_dict['body'] = body
        return email_dict

    def paginate_messages(self, service, response, max_results=None):
        threads = []
        if 'messages' in response:
            for i in response['messages']:
                threads.append(i['threadId'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(
                userId='me',
                pageToken=page_token).execute()
            for i in response['messages']:
                threads.append(i['threadId'])
            if max_results and len(threads) >= max_results:
                break
        return threads

    def get_recipient(self, email_data):
        if 'To' in email_data:
            to_field = email_data['To']
        else:
            try:
                headers = email_data['payload']['headers']
            except KeyError:
                return []
            to_field = [d['value'] for d in headers if d['name'] == 'To']
        sent_to = to_field.split(', ')
        names = []
        for i in sent_to:
            thing = (i.split(' <')[0])
            names.append(thing)
        return names

    def get_raw_from_id(self, service, email_id):
        try:
            msg = service.users().messages().get(
                userId='me',
                id=email_id,
                format='raw').execute()
            snip = msg['snippet']
            email = self.get_content(msg['raw'])
            return email, snip
        except HTTPError as e:
            print("Exception while scraping gmail: ", e)

    def get_meta_from_id(self, service, email_id):
        try:
            meta = service.users().messages().get(
                userId='me',
                id=email_id,
                format='metadata').execute()
            return meta
        except HTTPError as e:
            print("Exception while scraping gmail: ", e)

    def get_beg_thread(self, service, thread_id):
        try:
            thr = service.users().threads().get(
                userId='me',
                id=thread_id).execute()
            firstm = thr['messages'][0]['id']
            return self.get_raw_from_id(service, firstm)
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

        # Set up client
        http = creds.authorize(httplib2.Http())
        gmail = build('gmail', 'v1', http=http)
        print("[gmail] Scraping user: ", user_data.userid)

        # Get seed language tokens
        # Go through each token, seed a search to find threads we want to
        # search through
        thread_ids_per_token = {}
        for token in self.tokens:
            res = gmail.users().messages().list(
                userId='me',
                q='in:sent {0}'.format(token)).execute()
            thread_ids_per_token[token] = self.paginate_messages(
                gmail,
                res,
                max_results=self.num_threads
            )

        equalize_dict(thread_ids_per_token, self.num_threads)
        threads = set(thread for threads in thread_ids_per_token.values()
                      for thread in threads)
        data = { "text" : [],
                 "snippets" : [],
                 "people" : [] }
        for i, thread in enumerate(threads):
            email, snippet = self.get_beg_thread(gmail, thread)
            body = None
            if email['body'] is not None:
                body = email['body']
            people = self.get_recipient(email)
            data['text'].append(body)
            data['snippets'].append(snippet)
            data['people'].append(people)
        return data
