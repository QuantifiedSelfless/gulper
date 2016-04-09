from tornado import gen
from .debugprocessor import DebugProcessor
from .pr0nprocessor import Pr0nProcessor

import traceback


processors = [
    DebugProcessor(),
    Pr0nProcessor(),
]


# TODO: register the handlers given by the processors


@gen.coroutine
def process(user_data):
    result = {}
    for p in processors:
        try:
            print("starting: ", p.name)
            result[p.name] = yield p.process(user_data)
            print("done with: ", p.name)
        except Exception as e:
            result[p.name] = None
            print("Processor {} gave exception: {}".format(p.name, e))
            traceback.print_exc()
    return result
