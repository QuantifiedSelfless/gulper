from tornado import gen

import random
import string

from .lib.basescraper import BaseScraper


def random_string(min_size, max_size):
    length = random.randint(min_size, max_size)
    chars = string.ascii_letters
    return "".join(random.choice(chars) for _ in range(length))


class SampleScraper(BaseScraper):
    name = 'samplescraper'

    @gen.coroutine
    def scrape(self, user_data):
        num_items = random.randint(50, 150)
        texts = [
            {'text': random_string(1, 120)}
            for _ in range(num_items)
        ]
        return texts
