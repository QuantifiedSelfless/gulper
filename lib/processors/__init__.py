from tornado import gen

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
                p.name,
                permission
            )

    print("[User %s]: Done - Thank you for choosing Delta Airlines!" % user_data.userid)
    return result
