from tornado import gen

from nearpy import Engine
from nearpy.hashes import RandomBinaryProjections
import os
import pickle
import itertools as IT
from collections import Counter
import gender_guesser.detector as GenderDetector
from operator import itemgetter
import random

from .lib.handler import process_api_handler
from .lib.baseprocessor import BaseProcessor


POSES = (0, 1, 2)


class Pr0nProcessor(BaseProcessor):
    name = 'pr0n_processor'
    data = {}

    def __init__(self):
        super().__init__()
        self.gender_detector = GenderDetector.Detector(case_sensitive=False)
        try:
            fname = './data/{}/backend.pkl'.format(self.name)
            with open(fname, 'rb') as fd:
                self.pr0n_engine = pickle.load(fd)
            self.logger.info("Loaded backend from save state")
        except (IOError, ValueError):
            self.logger.info("Recreating backend engine")
            self.pr0n_engine = self.create_engine()
            self.read_pr0n()
            os.makedirs('./data/{}/'.format(self.name), exist_ok=True)
            with open(fname, 'wb+') as fd:
                pickle.dump(self.pr0n_engine, fd)

    def _get_img(self, img_hash):
        fname = "data/pr0n_processor/backend/{0[0]}/{0[1]}/{0}.pkl".format(img_hash)
        with open(fname, 'rb') as fd:
            return pickle.load(fd)

    def create_engine(self):
        rbp = RandomBinaryProjections('rbp', 8)
        return Engine(128, lshashes=[rbp])

    def get_gender(self, name):
        lookup = {
            'unknown': 0,
            'andy': 0,
            'male': -1,
            'female': 1,
            'mostly_male': -0.5,
            'mostly_female': 0.5,
        }
        first_name = name.split(" ")[0]
        gender = self.gender_detector.get_gender(first_name)
        return lookup[gender]

    def read_pr0n(self):
        num_added = 0
        for dirname, _, filenames in os.walk('./data/pr0n_processor/backend/'):
            if filenames:
                for filename in filenames:
                    if not filename.endswith('pkl'):
                        continue
                    filepath = os.path.join(dirname, filename)
                    filehash = filename.split('.')[0]
                    with open(filepath, 'rb') as fd:
                        data = pickle.load(fd)
                        if data['pose'] not in POSES:
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
            elif not any(f.get('pose') in POSES for f in photo['faces']):
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
        names_to_fbid = {}
        names_to_gender = {}
        user_engine = self.create_engine()
        for photo in photos:
            for face in photo['faces']:
                # skip photos with no facebook tags
                if not face['tags']:
                    continue
                if all(not self.valid_tag(t, {me}) for t in face['tags']):
                    continue
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
                        names_to_fbid[name] = tag['id']
                        names_to_gender[name] = self.get_gender(name)
                        names_to_scores[name]['images'][img] = distance
                        images_to_scores[img]['names'][name] = distance
        to_trim = set()
        for name, d in names_to_scores.items():
            if len(d['images']) > 10:
                images = list(d['images'].items())
                sorted(images, key=lambda x: x[1])
                d['images'] = dict(images[:10])
                to_trim -= d['images'].keys()
                to_trim.update(images[10:])
        for img_del in to_trim:
            images_to_scores.pop(img_del, None)
        blob = {
            'names_to_scores': names_to_scores,
            'names_to_gender': names_to_gender,
            'images_to_scores': images_to_scores,
            'names_to_fbid': names_to_fbid,
            'engine': user_engine,
            'gender_preference': [0, 0.0],
        }
        self.save_user_blob(blob, user_data)
        self.logger.info("Saved pr0n data")
        return True

    @gen.coroutine
    def set_preference(self, user, request):
        """
        Sets a users preference for a given photo
        """
        image_id = request.get_argument("id")
        preference = int(request.get_argument("preference"))
        data = self.load_user_blob(user)
        images_data = data['images_to_scores']
        names_data = data['names_to_scores']

        # increase the direct preference
        images_data[image_id]['scores']['direct'] += preference
        # increase all images that have the same person in them
        for name, dist in images_data[image_id]['names'].items():
            dist = float(dist)
            names_data[name]['scores']['name'] += preference / dist
            names_data[name]['normalization']['name'] += 1.0 / dist
            data['gender_preference'][0] += data['names_to_gender'][name] * preference
            data['gender_preference'][1] += 1.0
        # increase all images that are similar
        image_hash = images_data[image_id]['image_hash']
        for _, similar, dist in data['engine'].neighbours(image_hash):
            name, _ = similar.split("::", 1)
            dist = float(dist)
            names_data[name]['scores']['similar'] += preference / dist
            names_data[name]['normalization']['similar'] += 1.0 / dist
        self.save_user_blob(data, user)

    @gen.coroutine
    def get_sample(self, user, request):
        """
        Gets an image to show to the user
        """
        data = self.load_user_blob(user)
        images_to_scores = data['images_to_scores']
        if all(d['scores']['direct'] != 0 for d in images_to_scores.values()):
            return {'url': None, 'id': None}
        scored_names = dict(self.score_names(data))
        score_min = min(scored_names.values())
        score_max = max(scored_names.values())
        if not score_max:
            score_min = -1
            score_max = 1
        scored_names = {n: (s-score_min)/(score_max-score_min)
                        for n, s in scored_names.items()}
        for attempts in range(10):
            i2s = list(images_to_scores.items())
            random.shuffle(i2s)
            for img, img_data in i2s:
                if img_data['scores']['direct'] != 0:
                    continue
                for name, dist in img_data['names'].items():
                    if random.random() < scored_names[name]:
                        pick_id = img
                        pick_data = self._get_img(pick_id)
                        return {'url': pick_data['url'], 'id': pick_id,
                                'names': images_to_scores[pick_id]['names'],
                                'scores': scored_names}
        return {'url': None, 'id': None}

    @gen.coroutine
    def get_results(self, user, request):
        """
        Gets the results for a particular user.  Right now this is a simple
        metric... but it seems to be good enough.
        """
        data = self.load_user_blob(user)
        scores = self.score_names(data)
        names_to_fbid = data['names_to_fbid']
        names_to_scores = data['names_to_scores']
        results = []
        for name, score in scores:
            d = {"name": name, "score": score,
                 "fbid": names_to_fbid[name]}
            images = names_to_scores[name]['images']
            pick_id = min(images, key=images.get)
            d['url'] = self._get_img(pick_id)['url']
            results.append(d)
        return results

    def score_names(self, data):
        names_to_gender = data['names_to_gender']
        gender_pref = data['gender_preference'][0] / (data['gender_preference'][1] or 1)
        scores = []
        for name, data in data['names_to_scores'].items():
            name_score = data['scores']['name'] / \
                    (data['normalization']['name'] or 1.0)
            similarity_score = data['scores']['similar'] /  \
                (data['normalization']['similar'] or 1.0)
            gender_diff = abs(names_to_gender[name] - gender_pref)
            gender_diff = max(gender_diff - 0.75, 0.0)
            score = (name_score + 0.5 * similarity_score - gender_diff)
            scores.append((name, score))
        scores.sort(reverse=True, key=itemgetter(1))
        return scores

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
