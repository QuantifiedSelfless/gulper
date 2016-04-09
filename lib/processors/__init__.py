from tornado import gen
from .debugprocessor import DebugProcessor
#from .pr0nprocessor import Pr0nProcessor
from .ownupprocessor import OwnupProcessor

import traceback


processors = [
#    DebugProcessor(),
#    Pr0nProcessor(),
    OwnupProcessor()
]


# TODO: register the handlers given by the processors


@gen.coroutine
def process(user_data):
    result = {}
    for p in processors:
        try:
            result[p.name] = yield p.process(user_data)
        except Exception as e:
            result[p.name] = None
            print("Processor {} gave exception: {}".format(p.name, e))
            traceback.print_exc()
    return result
