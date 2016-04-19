from tornado import gen
import logging

from .lib.exhibit_permissions import ExhibitPermissions
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

FORMAT = '[%(levelname)1.1s %(asctime)s %(name)s:%(lineno)d] %(message)s'
logger = logging.getLogger("processor.process")

processors = [
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
    DebugProcessor()
]


@gen.coroutine
def process(user_data):
    result = {}
    exibperm = yield ExhibitPermissions.get_global()
    for p in processors:
        try:
            permission = yield p.process(user_data)
        except Exception:
            permission = None
            p.logger.exception("Excpetion while parsing user: %s",
                               user_data.userid)
        finally:
            result[p.name] = permission
            yield exibperm.save_permission(
                user_data.userid,
                user_data.meta['name'],
                p.name,
                permission
            )
    logger.info("Done Processing: " + user_data.userid)
    return result
