from tornado import gen

from nearpy import Engine
from nearpy.hashes import RandomBinaryProjections
import os
import pickle
from collections import defaultdict
import cryptohelper

from ..config import CONFIG
from .lib.utils import process_api_handler
from .lib.baseprocessor import BaseProcessor


class Pr0nProcessor(BaseProcessor):
    name = 'pr0n_processor'
    data = {}

    def __init__(self):
        super().__init__()
        try:
            fname = './data/pr0n/backend.pkl'
            with open(fname, 'rb') as fd:
                self.pr0n_engine = pickle.load(fd)
            self.logger.info("Loaded backend from save state")
        except (IOError, ValueError):
            self.logger.info("Recreating backend engine")
            self.pr0n_engine = self.create_engine()
            self.read_pr0n()
            with open(fname, 'wb+') as fd:
                pickle.dump(self.pr0n_engine, fd)

    def _get_img(self, img_hash):
        fname = "data/pr0n/backend/{0[0]}/{0[1]}/{0}.pkl".format(img_hash)
        with open(fname, 'rb') as fd:
            return pickle.load(fd)

    def create_engine(self):
        rbp = RandomBinaryProjections('rbp', 10)
        return Engine(128, lshashes=[rbp])

    def read_pr0n(self):
        num_added = 0
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
                        num_added += 1
        self.logger.info("Added backend pictures: {}".format(num_added))
        if not num_added:
            self.logger.error("PRON: No pictures added... try running "
                  "./scripts/create_pr0n_database.py")

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
        self.logger.info("Processing user: {}".format(user_data.userid))
        if not user_data.data.get('fbphotos'):
            return False
        photos = list(self.filter_photos(user_data.data['fbphotos']))
        if not photos:
            return False
        tag_lookup = defaultdict(list)
        for photo in photos:
            for face in photo['faces']:
                for tag in face['tags']:
                    N = self.pr0n_engine.neighbours(face['face_hash'])
                    closest_pr0ns = [
                        c
                        for c in N[:10]
                    ]
                    tag_lookup[tag['name']].append({
                        'photo': photo,
                        'face': face,
                        'tag': tag,
                        'closest_pr0n': closest_pr0ns,
                        'points': 0,
                    })
        image_to_name = defaultdict(list)
        for name, infos in tag_lookup.items():
            for info in infos:
                for imghash, img, dist in info['closest_pr0n']:
                    if img not in image_to_name:
                        image_to_name[img].append({
                            'names_dist': {},
                            'distance': dist,
                            'image_hash': imghash,
                            'scores': {'direct': 0, 'byname': 0, 'similar': 0},
                            'normalization': {'byname': 0, 'similar': 0}
                        })
                    image_to_name[img]['names_dist'][name] = dist
        user_engine = self.create_engine()
        for i, (tag, data) in enumerate(tag_lookup.items()):
            for d in data:
                _id = "{}::{}".format(d['tag']['name'], d['photo']['id'])
                user_engine.store_vector(d['face']['face_hash'], _id)
        blob = {
            'tag_lookup': tag_lookup,
            'engine': user_engine,
            'image_to_name': image_to_name
        }
        self.save_user(blob, user_data)
        self.logger.info("Saved pr0n data")

    def save_user(self, blob, user_data):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/pr0n/user/{}.pkl".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                pickle.dump(blob, fd)
        else:
            blob_enc = user_data.encrypt_blob(blob)
            filename = "./data/pr0n/user/{}.enc".format(user_data.userid)
            with open(filename, 'wb+') as fd:
                fd.write(blob_enc)

    def load_user(self, user):
        if CONFIG.get('_mode') == 'dev':
            filename = "./data/pr0n/user/{}.pkl".format(user.userid)
            with open(filename, 'rb') as fd:
                return pickle.load(fd)
        else:
            filename = "./data/pr0n/user/{}.enc".format(user.userid)
            with open(filename, 'rb') as fd:
                blob = fd.read()
                return user.decrypt_blob(blob)

    @gen.coroutine
    def get_sample(self, user, request):
        """
        Gets an image to show to the user
        """
        data = self.load_user(user)
        images = data['image_to_name']
        # filter images the user hasn't seen yet
        candidates = [
            (img, d['scores'])
            for img, d in images.items()
            if d['scores']['direct'] == 0
        ]
        # find the image we have the least amount of data on
        pick_id, pick_score = None, 1e8
        for img, d in images.items():
            score = abs(sum(d['scores'].values()))
            if score < pick_score:
                pick_id, pick_score = img, pick_score
        # no pick id? then the client should show results
        if pick_id is None:
            return {'url': None, 'id': None}
        pick_data = self._get_img(pick_id)
        return {'url': pick_data['url'], 'id': pick_id}

    @gen.coroutine
    def set_preference(self, user, request):
        """
        Sets a users preference for a given photo
        """
        image_id = request.get_argument("id")
        preference = int(request.get_argument("preference"))
        data = self.load_user(user)
        images = data['image_to_name']
        for d in images[image_id]:
            d['scores']['direct'] += preference
        # increase all images that have the same person in them
        names = set(images[image_id]['names_dist'].keys())
        for image, d in images:
            if image != image_id and d['name'] in names:
                d['scores']['name'] += preference
                d['normalization']['name'] += 1
        # increase all images that are similar
        image_hash = images[image_id]['image_hash']
        for _, similar, dist in data['engine'].neighbours(image_hash):
            similar_name = similar.split(":::", 1)[0]
            for image, datas in images:
                for d in datas:
                    if similar_name == d['name']:
                        d['scores']['similar'] += preference / dist
                        d['normalization']['similar'] += 1.0 / dist
        self.save_user(data, user)

    @gen.coroutine
    def get_results(self, user, request):
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
            ('sample', self.get_sample),
            ('preference', self.set_preference),
            ('results', self.get_results),
        ]
