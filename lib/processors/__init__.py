from tornado import gen
from .sampleprocessor import SampleProcessor


processors = [
    SampleProcessor(),
]


# TODO: register the handlers given by the processors


@gen.coroutine
def process(user_data):
    result = yield {
        p.name: p.process(user_data)
        for p in processors
    }
    return result
