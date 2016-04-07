from tornado import gen
from .utils import process_api_handler

import re


class SampleProcessor(object):
    name = 'news_processor'

    def fb_proxy(self, prof):
        if 'political' in prof:
            dem = re.search('dem', prof['political'])
            liberal = re.search('liberal', prof['political'])
            repub = re.search('repub', prof['political'])
            cons = re.search('conservative', prof['political'])
            if dem:
                return 2
            if liberal:
                return 1
            if repub:
                return 4
            if cons:
                return 6
        else:
            return None


    @gen.coroutine
    def process(self, user_data):
        """
        Process the scraped data inside of user_data and save it locally.  It
        can save it to file, or a database... no one really cares
        """
        data = {}
        data['category'] = None
        if user_data['fbprofile'] is not False:
            data['category'] = self.fb_proxy(user_data['fbprofile'])
        if data['category'] is None:
            if 'reddit' in user_data:




        print("Processing user: ", user_data.userid)
        userid = user_data.userid
        

    @gen.coroutine
    def get_category(self, user, request):
        """
        Returns relevant data that the exhibits may want to know
        """
        return self.data.get(userid, 'userid not found')

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('news_category', self.get_category),
        ]
