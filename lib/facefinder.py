"""
Good example:
    http://dlib.net/face_detector.py.html
"""
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from io import BytesIO
from PIL import Image
import numpy as np
import dlib

detector = dlib.get_frontal_face_detector()
http_client = AsyncHTTPClient()


@gen.coroutine
def find_faces_url(url):
    """
    Given a URL to an image, find all the faces.  The returned list has
    dictionaries with the following fields:
        rect -> bounding rectangle around the face
        score -> score of the face detection (higher == better)
        pose -> index of sub-detector matched which roughly corresponds to pos
                (0 is best)
    """
    image_req = yield http_client.fetch(url)
    if image_req.code != 200:
        return []
    image_fd = BytesIO(image_req.body)
    image = Image.open(image_fd)
    image_np = np.array(image)
    rects, scores, poses = detector.run(image_np, 1)
    return [{"rect": r, "score": s, "pose": p}
            for r, s, p in zip(rects, scores, poses)]
