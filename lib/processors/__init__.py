from tornado import gen
import logging

from .debugprocessor import DebugProcessor
from .pr0nprocessor import Pr0nProcessor
from .truthprocessor import TruthProcessor
from .mirrorprocessor import MirrorProcessor
from .newsprocessor import NewsProcessor
from .ownupprocessor import OwnupProcessor
from .interviewprocessor import InterviewProcessor
from .ameliaprocessor import AmeliaProcessor
from .mentalhealthprocessor import MentalHealthProcessor
from .trackedprocessor import TrackedProcessor
from .recommenderprocessor import RecommenderProcessor
from .romanceprocessor import RomanceProcessor
from .tosprocessor import TOSProcessor
from .deleteprocessor import DeleteProcessor

FORMAT = '[%(levelname)1.1s %(asctime)s %(name)s:%(lineno)d] %(message)s'
logger = logging.getLogger("processor.process")

processors = [
    DebugProcessor(),
    Pr0nProcessor(),
    TruthProcessor(),
    MirrorProcessor(),
    NewsProcessor(),
    OwnupProcessor(),
    InterviewProcessor(),
    AmeliaProcessor(),
    MentalHealthProcessor(),
    RecommenderProcessor(),
    TrackedProcessor(),
    RomanceProcessor(),
    TOSProcessor(),
    DeleteProcessor(),
]


@gen.coroutine
def process(user_data):
    result = {}
    logger.info("Starting to Process: " + user_data.userid)
    for p in processors:
        permission = yield p.start(user_data)
        result[p.name] = permission
    logger.info("Done Processing: {}: {}".format(user_data.userid,
                                                 result[p.name]))
    return result
