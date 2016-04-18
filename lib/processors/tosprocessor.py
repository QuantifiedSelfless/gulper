from tornado import gen
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


def question_similarity(A, B):
    return len(A & B) / float(len(A | B))


class TOSProcessor(BaseProcessor):
    name = 'tos_processor'
    auth = False

    def __init__(self):
        super().__init__()

    @gen.coroutine
    def go_ahead(self, user, request):
        """
        Do I really need this?
        """
        return True

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('tos', self.go_ahead),
        ]
