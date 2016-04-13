from tornado import gen
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor
from .lib.jaccard import jaccard_rec


class RecommnedProcessor(BaseProcessor):
    name = 'recommend_processor'

    def __init__(self):
        super().__init__()

    @gen.coroutine
    def process(self, user_data):
        # This game requires no data
        return True

    @gen.coroutine
    def recommend_stuff(self, user, request):
        """
        Returns relevant data that the exhibits may want to know
        """
        ans = request.get_argument('answers')
        data = jaccard_rec(ans)
        resp = {"recommendations": data}
        return resp

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('recommend', self.recommend_stuff),
        ]
