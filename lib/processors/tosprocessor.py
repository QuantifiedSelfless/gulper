from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


class TOSProcessor(BaseProcessor):
    name = 'tos_processor'
    auth = False

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return []
