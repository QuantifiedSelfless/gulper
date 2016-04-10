from tornado import gen

from .lib.exhibit_permissions import ExhibitPermissions
from .debugprocessor import DebugProcessor
from .pr0nprocessor import Pr0nProcessor


processors = [
    DebugProcessor(),
    Pr0nProcessor(),
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
    return result
