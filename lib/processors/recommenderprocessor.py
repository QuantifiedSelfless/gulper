from tornado import gen
import ujson as json
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


def question_similarity(A, B):
    return len(A & B) / float(len(A | B))


class RecommenderProcessor(BaseProcessor):
    name = 'recommend_processor'

    def __init__(self):
        with open("lib/processors/data/recommender.json") as fd:
            sample_responses = json.load(fd)
            self.sample_responses = [r
                                     for r in sample_responses]
            self.sample_responses_db = list(map(set, self.sample_responses))
        super().__init__()

    def recommend(self, user_answers):
        uas = set(user_answers)
        idx, _ = max(
            enumerate(self.sample_responses_db),
            key=lambda x: question_similarity(x[1], uas)
        )
        return self.sample_responses[idx]

    @gen.coroutine
    def process(self, user_data):
        # This game requires no data
        return True

    @gen.coroutine
    def recommend_stuff(self, user, request):
        """
        Returns relevant data that the exhibits may want to know
        """
        ans = request.get_arguments('answers')
        data = self.recommend(ans)
        return {"recommendations": data}

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('recommend', self.recommend_stuff),
        ]
