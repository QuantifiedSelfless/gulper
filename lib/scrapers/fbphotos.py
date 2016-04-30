from tornado import gen

from facebook import GraphAPI
from lib.facefinder import find_faces_url
from lib.config import CONFIG
from dlib import point

from .lib.utils import facebook_paginate
from .lib.basescraper import BaseScraper


class FBPhotosScraper(BaseScraper):
    name = 'fbphotos'

    @property
    def num_images_per_user(self):
        if CONFIG['_mode'] == 'prod':
            return 200
        return 50

    @gen.coroutine
    def scrape(self, user_data):
        try:
            oauth = user_data.services['facebook']['access_token']
        except KeyError:
            return False
        graph = GraphAPI(access_token=oauth)
        photos_friends_profile = yield self.get_friends_profile(graph)

        photos_me = yield facebook_paginate(
            graph.get_connections(
                'me',
                'photos',
                fields='images,tags.limit(50)'
            ),
            max_results=self.num_images_per_user
        )
        photos_uploaded = yield facebook_paginate(
            graph.get_connections(
                'me',
                'photos',
                fields='images,tags.limit(50)',
                type='uploaded'
            ),
            max_results=self.num_images_per_user
        )
        photos_friends_raw = yield facebook_paginate(
            graph.get_connections(
                'me',
                'friends',
                fields='photos.limit(1){tags.limit(100),images}'
            ),
            max_results=self.num_images_per_user
        )
        photos_friends = []
        for d in photos_friends_raw:
            try:
                for photo in d['photos']['data']:
                    photos_friends.append(photo)
            except KeyError:
                pass

        photos_me = yield self.parse_photos(graph, photos_me)
        photos_uploaded = yield self.parse_photos(graph, photos_uploaded)
        photos_friends = yield self.parse_photos(graph, photos_friends)
        return {'me': photos_me, 'friends': photos_friends,
                'friends_profile': photos_friends_profile,
                'uploaded': photos_uploaded}

    @gen.coroutine
    def get_friends_profile(self, graph):
        friends_raw = yield facebook_paginate(
            graph.get_connections(
                'me',
                'feed',
                fields='from'
            ),
            max_results=self.num_images_per_user,
        )
        friends = {d['from']['id']: d['from']['name']
                   for d in friends_raw}
        pictures = []
        profile_pic = 'http://graph.facebook.com/{}/picture?type=large'
        for i, (fid, fname) in enumerate(friends.items()):
            photo = {
                'url': profile_pic.format(fid),
                'id': 'img-' + fid,
            }

            self.logger.debug("Friend face finding: %d / %d", i, len(friends))
            faces = yield find_faces_url(photo['url'], hash_face=True)
            # go through the faces _we_ found and interpolate those results
            # with the tags from the image
            for face in faces:
                face['tags'] = [{'name': fname, 'id': fid}]
            photo['faces'] = faces
            pictures.append(photo)
        return pictures

    @gen.coroutine
    def parse_photos(self, graph, photos):
        for i, photo in enumerate(photos):
            if 'tags' not in photo:
                continue
            photo['images'].sort(key=lambda x: x['height']*x['width'])
            image_url = photo['images'][-1]
            width, height = image_url['width'], image_url['height']
            people = [
                (
                    point(int(t['x']*width/100.0),
                          int(t['y']*height/100.0)),
                    t
                )
                for t in photo['tags']['data']
                if t.get('x') and t.get('y')
            ]
            self.logger.debug("Face finding: %d / %d", i, len(photos))
            faces = yield find_faces_url(image_url['source'], hash_face=True)
            # go through the faces _we_ found and interpolate those results
            # with the tags from the image
            for face in faces:
                face['tags'] = []
                for p, tag in people:
                    if face['rect'].contains(p):
                        face['tags'].append(tag)
            photo['faces'] = faces
        return photos
