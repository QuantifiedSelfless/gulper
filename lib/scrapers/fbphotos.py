from tornado import gen

from facebook import GraphAPI
from lib.facefinder import find_faces_url
from lib.config import CONFIG
from dlib import point
from .utils import facebook_paginate


class FBPhotosScraper(object):
    name = 'fbphotos'

    @property
    def num_images_per_user(self):
        if CONFIG['_mode'] == 'prod':
            return 1000
        return 100

    @gen.coroutine
    def scrape(self, user_data):
        try:
            oauth = user_data.services['facebook']['access_token']
        except KeyError:
            return False
        graph = GraphAPI(access_token=oauth)
        print("[fbphotos] Scraping user: ", user_data.userid)
        photos = yield facebook_paginate(
            graph.get_connections(
                'me',
                'photos',
                fields='picture,images,tags.limit(50),name,place'
            ),
            max_results=self.num_images_per_user
        )
        for photo in photos:
            photo['images'].sort(key=lambda x: x['height']*x['width'])
            image = photo['images'][-1]
            width, height = image['width'], image['height']
            people = [
                (
                    point(int(t['x']*width/100.0),
                          int(t['y']*height/100.0)),
                    t
                )
                for t in photo['tags']['data']
            ]
            faces = yield find_faces_url(image['source'])
            # go through the faces _we_ found and interpolate those results
            # with the tags from the image
            for face in faces:
                face['tags'] = []
                for p, tag in people:
                    if face['rect'].contains(p):
                        face['tags'].append(tag)
            photo['faces'] = faces
        return photos
