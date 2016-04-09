from tornado import gen

from nearpy import Engine
from nearpy.hashes import RandomBinaryProjections
import os
import pickle
import itertools as IT
from collections import Counter
from operator import itemgetter

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
        rbp = RandomBinaryProjections('rbp', 8)
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
            elif not any(f.get('face_hash', None) is not None
                         for f in photo['faces']):
                continue
            yield photo

    def valid_tag(self, tag, names):
        return tag['name'] not in names and tag.get('id') is not None

    @gen.coroutine
    def process(self, user_data):
        """
        Go through all the tagged facebook pictures from the user and creates a
        nearpy structure for easy similarity lookup
        """
        self.logger.info("Processing user: {}".format(user_data.userid))
        if not user_data.data.get('fbphotos'):
            self.logger.debug("No FB photos found for: %s", user_data.userid)
            return False
        photos_me_and_friends = IT.chain.from_iterable(
            user_data.data['fbphotos'].values()
        )
        # NOTE: is there a better way to figure out the name of the current
        # user within the facebook tagging universe?  i assume one of the other
        # facebook scrapers is going to extract that information somewhere and
        # we'll be able to use it here instead of doing this crazy tag counting
        me_candidates = Counter(t['name']
                                for photo in user_data.data['fbphotos']['me']
                                for face in photo['faces']
                                for t in face['tags'])
        me, _ = me_candidates.most_common(1)[0]

        photos = list(self.filter_photos(photos_me_and_friends))
        if not photos:
            self.logger.debug("No useful photos found for: %s",
                              user_data.userid)
            return False
        names_to_scores = {}
        images_to_scores = {}
        user_engine = self.create_engine()
        for photo in photos:
            for face in photo['faces']:
                # skip photos with no facebook tags
                if not face['tags']:
                    continue
                if all(not self.valid_tag(t, {me}) for t in face['tags']):
                    continue
                # skip photos where the person isn't looking straight at the
                # camera (zero is the subclassifier index in dlib for that)
                # if face['pose'] != 0:
                    # continue
                N = self.pr0n_engine.neighbours(face['face_hash'])
                closest_pr0ns = [
                    c
                    for c in N[:10]
                    if c[-1] < 0.75
                ]
                if not closest_pr0ns:
                    continue
                for tag in face['tags']:
                    if not self.valid_tag(tag, {me}):
                        continue
                    _id = "{}::{}".format(tag['name'], photo['id'])
                    user_engine.store_vector(face['face_hash'], _id)
                for img_hash, img, distance in closest_pr0ns:
                    if not any(self.valid_tag(t, {me}) for t in face['tags']):
                        continue
                    images_to_scores[img] = {
                        'scores': {'direct': 0},
                        'names': {},
                        'image_hash': img_hash,
                    }
                    for tag in face['tags']:
                        name = tag['name']
                        if not self.valid_tag(tag, {me}):
                            continue
                        if name not in names_to_scores:
                            names_to_scores[name] = {
                                'scores': {'similar': 0, 'name': 0},
                                'normalization': {'similar': 0, 'name': 0},
                                'images': {},
                            }
                        names_to_scores[name]['images'][img] = distance
                        images_to_scores[img]['names'][name] = distance
        blob = {
            'names_to_scores': names_to_scores,
            'images_to_scores': images_to_scores,
            'engine': user_engine,
        }
        self.save_user(blob, user_data)
        self.logger.info("Saved pr0n data")
        return True

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
        images_data = data['images_to_scores']
        names_data = data['names_to_scores']
        # filter images the user hasn't seen yet
        candidates = [
            (img, d)
            for img, d in images_data.items()
            if d['scores']['direct'] == 0
        ]
        # find the image we have the least amount of data on
        pick_id, pick_score = None, 1e8
        for img, d in candidates:
            # this score is arbitrary... i figured something that would single
            # out images related to names that we don't have much information
            # about and weight the name contributions by how similar the name
            # is to the image.
            norm = sum(dist for dist in d['names'].values())
            score = sum(dist * (names_data[name]['scores']['name'] +
                                names_data[name]['scores']['similar'] +
                                dist)
                        for name, dist in d['names'].items())
            score /= float(norm or 1.0)
            if 0 <= score < pick_score:
                pick_id, pick_score = img, score
        # no pick id? then the client should show results
        if pick_id is None:
            return {'url': None, 'id': None}
        pick_data = self._get_img(pick_id)
        return {'url': pick_data['url'], 'id': pick_id,
                'names': images_data[pick_id]['names']}

    @gen.coroutine
    def set_preference(self, user, request):
        """
        Sets a users preference for a given photo
        """
        image_id = request.get_argument("id")
        preference = int(request.get_argument("preference"))
        data = self.load_user(user)
        images_data = data['images_to_scores']
        names_data = data['names_to_scores']

        # increase the direct preference
        images_data[image_id]['scores']['direct'] += preference
        # increase all images that have the same person in them
        for name, dist in images_data[image_id]['names'].items():
            dist = float(dist)
            names_data[name]['scores']['name'] += preference / dist
            names_data[name]['normalization']['name'] += 1.0 / dist
        # increase all images that are similar
        image_hash = images_data[image_id]['image_hash']
        for _, similar, dist in data['engine'].neighbours(image_hash):
            name, _ = similar.split("::", 1)
            dist = float(dist)
            names_data[name]['scores']['similar'] += preference / dist
            names_data[name]['normalization']['similar'] += 1.0 / dist
        self.save_user(data, user)

    @gen.coroutine
    def get_results(self, user, request):
        """
        Gets the results for a particular user.  Right now this is a simple
        metric... but it seems to be good enough.
        """
        data = self.load_user(user)
        scores = []
        for name, data in data['names_to_scores'].items():
            name_score = data['scores']['name'] / \
                    (data['normalization']['name'] or 1.0)
            similarity_score = data['scores']['similar'] /  \
                (data['normalization']['similar'] or 1.0)
            score = name_score + 0.5 * similarity_score
            scores.append((name, score))
        scores.sort(reverse=True, key=itemgetter(1))
        return [{"name": n, "score": s} for n, s in scores]

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
