from tornado import gen

from .lib.baseprocessor import BaseProcessor


class DebugProcessor(BaseProcessor):
    name = 'debug_processor'

    @gen.coroutine
    def process(self, user_data):
        """
        Save user data for inspection
        """
        self.logger.info("Saving user scrape data")
        self.save_user_blob(user_data.data, user_data)
        self.logger.info("Saved user: " + user_data.userid)
        return True

    def load_scrape(self, user_data):
        return self.load_user_blob(user_data)
