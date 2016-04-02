from tornado import gen

from nearpy import Engine
from nearpy.hashes import RandomBinaryProjections
import os
import pickle
from collections import defaultdict

from .utils import process_api_handler


class Pr0nProcessor(object):
    name = 'pr0n_processor'
    data = {}

    def __init__(self):
        self.pr0n_engine = self.create_engine()
        self.read_pr0n()

    def create_engine(self):
        rbp = RandomBinaryProjections('rbp', 24)
        return Engine(128, lshashes=[rbp])

    def read_pr0n(self):
        for dirname, _, filenames in os.walk('./data/pr0n/backend/'):
            if filenames:
                for filename in filenames:
                    if not filename.endswith('pkl'):
                        continue
                    filepath = os.path.join(dirname, filename)
                    filehash = filename.split('.')[0]
                    with open(filepath, 'rb') as fd:
                        data = pickle.load(fd)
                        if data['pose'] != 0:
                            continue
                        self.pr0n_engine.store_vector(data['face_hash'],
                                                      filehash)

    def filter_photos(self, photos):
        for photo in photos:
            if not photo.get('faces'):
                continue
            elif not any(f.get('pose') == 0 for f in photo['faces']):
                continue
            elif not any(f.get('face_hash', None) is not None for f in photo['faces']):
                continue
            yield photo

    @gen.coroutine
    def process(self, user_data):
        """
        Go through all the tagged facebook pictures from the user and creates a
        nearpy structure for easy similarity lookup
        """
        print("PR0N: Processing user: ", user_data.userid)
        if not user_data.data.get('fbphotos'):
            return False
        photos = list(self.filter_photos(user_data.data['fbphotos']))
        if not photos:
            return False
        tag_lookup = defaultdict(list)
        for photo in photos:
            for face in photo['faces']:
                for tag in face['tags']:
                    tag_lookup[tag['name']].append({
                        'photo': photo,
                        'face': face,
                        'tag': tag,
                    })
        user_engine = self.create_engine()
        for i, (tag, data) in enumerate(tag_lookup.items()):
            for d in data:
                _id = "{}::{}".format(d['tag']['id'], d['photo']['id'])
                user_engine.store_vector(d['face']['face_hash'], _id)
        blob = {'tag_lookup': tag_lookup, 'engine': user_engine}
        blob_enc = user_data.encrypt_blob(blob)
        filename = "./data/pr0n/user/{}.enc".format(user_data.userid)
        with open(filename, 'wb+') as fd:
            fd.write(blob_enc)
        print("Saved pr0n data at: ", filename)

    @gen.coroutine
    def set_preference(self, userid, request, private_key=None):
        """
        Sets a users preference for a given photo
        """
        pass

    @gen.coroutine
    def get_results(self, userid, request, private_key=None):
        """
        Gets the results for a particular user
        """
        pass

    @process_api_handler
    def register_handlers(self):
        """
        Registers any http handlers that this processor wants to have availible
        to exhibits
        """
        return [
            ('preference', self.set_preference),
            ('results', self.get_results),
        ]

