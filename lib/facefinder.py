"""
Good example:
    http://dlib.net/face_detector.py.html
"""
from tornado import gen
from tornado.httpclient import HTTPError
from io import BytesIO
from PIL import Image
import numpy as np
import dlib
from . import openface
from . import httpclient

detector = dlib.get_frontal_face_detector()


def find_faces_buffer(image_fd, hash_face=False, upsample=1):
    image = Image.open(image_fd)
    image_np = np.array(image)
    rects, scores, poses = detector.run(image_np, 1)
    data = [{"rect": r, "score": s, "pose": p}
            for r, s, p in zip(rects, scores, poses)]
    for d in data:
        d['face_hash'] = None
        if hash_face:
            d['face_hash'] = openface.hash_face(image_np, bb=d['rect'])
    return data


@gen.coroutine
def find_faces_url(url, hash_face=False, upsample=1):
    """
    Given a URL to an image, find all the faces.  The returned list has
    dictionaries with the following fields:
        rect -> bounding rectangle around the face
        score -> score of the face detection (higher == better)
        pose -> index of sub-detector matched which roughly corresponds to pos
                (0 is best)
    """
    try:
        image_req = yield httpclient.fetch(url, request_timeout=30.0)
    except HTTPError as e:
        print("Exception while fetching image URL: {}: {}".format(url, e))
        return []
    if image_req.code != 200:
        return []
    image_fd = BytesIO(image_req.body)
    return find_faces_buffer(image_fd, hash_face=hash_face, upsample=upsample)
