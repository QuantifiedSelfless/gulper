import sys
import os
from tornado import gen
from tornado import ioloop
from tornado.httpclient import HTTPError
import dlib
from PIL import Image
import numpy as np
import pickle
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from io import BytesIO
import hashlib
import itertools as IT

sys.path.append(os.path.abspath(os.path.join(__file__,  '../..')))
from lib import openface
from lib import httpclient


detector = dlib.get_frontal_face_detector()


def unique_id(url):
    m = hashlib.md5()
    m.update(url.encode())
    return m.digest().hex()


@gen.coroutine
def process_actor(name, gender, url,
                  data_path='./data/pr0n_processor/backend/'):
    uid = unique_id(url)
    os.makedirs(os.path.join(data_path, uid[0], uid[1]), exist_ok=True)
    filepath = os.path.join(data_path, uid[0], uid[1], uid)
    if os.path.exists(filepath + '.pkl'):
        return

    try:
        page_data = yield httpclient.fetch(url, request_timeout=10)
    except HTTPError:
        return
    soup = BeautifulSoup(page_data.body, 'html.parser')
    img = soup.find('img', title=re.compile("Portrait of"))
    img_src = img.attrs['src']

    try:
        image_req = yield httpclient.fetch(img_src, request_timeout=10)
    except HTTPError:
        return
    image_fd = BytesIO(image_req.body)
    try:
        image = Image.open(image_fd)
    except OSError:
        return
    image_np = np.array(image)
    try:
        rects, scores, poses = detector.run(image_np)
    except RuntimeError:
        return
    if len(scores) != 1:
        return
    try:
        face_hash = yield openface.hash_face(image_np, bb=rects[0])
    except:
        return
    data = {
        'url': url,
        'uid': uid,
        'rects': rects[0],
        'pose': poses[0],
        'score': scores[0],
        'face_hash': face_hash,
        'name': name,
        'gender': gender,
    }
    try:
        image.save(filepath + '.jpg')
        with open(filepath + '.pkl', 'wb+') as fd:
            pickle.dump(data, fd, protocol=-1)
        print(name, gender, url, uid)
    except OSError:
        return


@gen.coroutine
def process_porndb():
    base = 'http://www.adultfilmdatabase.com/browse.cfm?' \
           'type=actor&page={}&imageFlag=1'
    for page in IT.count(1):
        url = base.format(page)
        print(url)
        data = yield httpclient.fetch(url)
        soup = BeautifulSoup(data.body, 'html.parser')
        actors = []
        for row in soup.findAll("tr"):
            cells = row.findAll("td")
            if len(cells) != 7:
                continue
            try:
                name = cells[0].getText().strip()
                gender = cells[1].getText().strip()
                page = urljoin(url, cells[0].find('a').attrs['href'])
                actors.append((name, gender, page))
            except (IndexError, AttributeError):
                continue
        yield list(IT.starmap(process_actor, actors))
        yield gen.sleep(5)


if __name__ == "__main__":
    ioloop.IOLoop().instance().run_sync(process_porndb)
