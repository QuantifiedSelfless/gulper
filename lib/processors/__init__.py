from tornado import gen
from .debugprocessor import DebugProcessor
from .pr0nprocessor import Pr0nProcessor
from .truthprocessor import TruthProcessor
from .mirrorprocessor import MirrorProcessor
from .newsprocessor import NewsProcessor
from .ownupprocessor import OwnupProcessor

import traceback


processors = [
    DebugProcessor(),
    Pr0nProcessor(),
    TruthProcessor(),
    MirrorProcessor(),
    NewsProcessor()
    OwnupProcessor()
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
