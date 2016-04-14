from tornado import gen
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


class RomanceProcessor(BaseProcessor):
    name = 'romance_processor'

    def __init__(self):
        super().__init__()

    @gen.coroutine
    def process(self, user_data):
        return True

    @gen.coroutine
    def romantic(self, user, request):
        """
        Returns relevant data that the exhibits may want to know
        TODO: Decide key we encrypt with and what the expected request will be
        """
        return True

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('romance', self.romantic),
        ]

