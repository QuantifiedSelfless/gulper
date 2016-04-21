from tornado import gen

from .lib.handler import process_api_handler
from .lib.baseprocessor import BaseProcessor
from .lib.exhibit_permissions import ExhibitPermissions

from ..rfidb import RFIDB


# TODO not this...  we should be able to fix this up after issue #40 is
# resolved.  Right now there is no clean way to do this so we may as well do
# the most convinient until that technical debt is taken care of.
import rethinkdb as r
from ..config import CONFIG
@gen.coroutine
def delete_user_auth(user):
    db = 'pilot'
    if CONFIG.get("_mode") == "prod":
        db = 'showtime'
    conn = yield r.connect(db=db)
    result = yield r.table('auth').get(user.userid).delete().run(conn)
    return bool(result.get('deleted'))


@gen.coroutine
def wrap_delete(processor, user_data):
    try:
        processor.logger.debug("Deleting data")
        result = yield processor.delete_data(user_data)
    except:
        result = None
        processor.logger.exception("Could not delete data: " +
                                   user_data.userid)
    return result


class DeleteProcessor(BaseProcessor):
    name = 'delete_processor'
    auth = False

    @gen.coroutine
    def delete_user(self, user, request):
        from . import processors
        result = {}
        exibperm = yield ExhibitPermissions.get_global()
        rfidb = yield RFIDB.get_global()
        result['permissions'] = yield exibperm.delete_permissions(user)
        result['rfid'] = yield rfidb.delete_user(user)
        result['processors'] = yield {p.name: wrap_delete(p, user)
                                      for p in processors}
        result['auth'] = yield delete_user_auth(user)
        result['usreid'] = user.userid
        return result

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('delete_data', self.delete_user),
        ]
