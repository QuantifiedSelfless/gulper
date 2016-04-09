from tornado import gen
import pickle


class DebugProcessor(object):
    name = 'debug_processor'
    data = {}

    @gen.coroutine
    def process(self, user_data):
        """
        Save user data for inspection
        """
        filename = "./data/debug/{}.pkl".format(user_data.userid)
        with open(filename, 'wb+') as fd:
            pickle.dump(user_data.data, fd)
        print("Saved used {} to {}".format(user_data.userid, filename))
        return True

    def register_handlers(self):
        return []
