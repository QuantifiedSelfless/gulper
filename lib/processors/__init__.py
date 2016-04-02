from tornado import gen
from .sampleprocessor import SampleProcessor
from .debugprocessor import DebugProcessor

import traceback


processors = [
    SampleProcessor(),
    DebugProcessor(),
]


# TODO: register the handlers given by the processors


@gen.coroutine
def process(user_data):
    result = {}
    for p in processors:
        try:
            result[p.name] = p.process(user_data)
        except:
            result[p.name] = None
            print("Processor {} gave exception: {}".format(p.name, e))
            traceback.print_exc()
    return result
