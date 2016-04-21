from tornado import gen
import logging
import pickle
import os

from ...config import CONFIG
from .handler import process_api_handler, authentication
from .exhibit_permissions import ExhibitPermissions


FORMAT = '[%(levelname)1.1s %(asctime)s %(name)s:%(lineno)d] %(message)s'


class BaseProcessor(object):
    auth = True

    def __init__(self, *args, **kwargs):
        logging.basicConfig(format=FORMAT)
        self.logger = logging.getLogger("processor." + self.name)

    @gen.coroutine
    def process(self, user_data):
        return True

    @gen.coroutine
    def start(self, user_data):
        exibperm = yield ExhibitPermissions.get_global()
        try:
            self.logger.debug("Starting for " + user_data.userid)
            permission = yield self.process(user_data)
        except Exception:
            permission = None
            self.logger.exception("Excpetion while parsing user: %s",
                                  user_data.userid)
        finally:
            self.logger.debug("Saving permission for: %s: %s",
                              user_data.userid, permission)
            yield exibperm.save_permission(
                user_data,
                self.name,
                permission
            )
        return permission

    @authentication(False)
    @gen.coroutine
    def delete_data(self, user_data):
        """
        Default delete_data will only delete permissions for the given user and
        any data saved using BaseProcessor's save_user_blob method.
        """
        filedata = dict(name=self.name, uid=user_data.userid)
        try:
            filename = "./data/{name}/user/{uid}.pkl".format(**filedata)
            os.remove(filename)
        except FileNotFoundError:
            pass
        try:
            filename = "./data/{name}/user/{uid}.enc".format(**filedata)
            os.remove(filename)
        except FileNotFoundError:
            pass
        return True

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return []

    def save_user_blob(self, blob, user):
        filedata = dict(name=self.name, uid=user.userid)
        os.makedirs("./data/{name}/user".format(**filedata), exist_ok=True)
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/{name}/user/{uid}.pkl".format(**filedata)
            with open(filename, 'wb+') as fd:
                pickle.dump(blob, fd)
        else:
            blob_enc = user.encrypt_blob(blob)
            filename = "./data/{name}/user/{uid}.enc".format(**filedata)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user_blob(self, user):
        filedata = dict(name=self.name, uid=user.userid)
        try:
            filename = "./data/{name}/user/{uid}.pkl".format(**filedata)
            with open(filename, 'rb') as fd:
                return pickle.load(fd)
        except IOError:
            filename = "./data/{name}/user/{uid}.enc".format(**filedata)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    def load_keywords(self, datafile):
        filename = './lib/processors/data/' + datafile
        try:
            with open(filename) as fd:
                return [kw.strip() for kw in fd]
        except IOError:
            self.logger.exception("Could not load keywords: " + filename)
