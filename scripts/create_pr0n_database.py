import sys, os
from tornado import gen
from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient, HTTPError
import dlib
from PIL import Image
import numpy as np
import praw
import pickle

from io import BytesIO
import hashlib

sys.path.append(os.path.abspath(os.path.join(__file__,  '../..')))
from lib import openface


http_client = AsyncHTTPClient()
detector = dlib.get_frontal_face_detector()


def normalize_url(url):
    if url[-3:] in ('jpg', 'png'):
        return url
    elif 'imgur.com' in url and '/a/' not in url:
        return url + '.jpg'
    raise ValueError


def unique_id(url):
    m = hashlib.md5()
    m.update(url.encode())
    return m.digest().hex()


def skip_unfound(_iter):
    while True:
        try:
            yield next(_iter)
        except StopIteration:
            return
        except Exception:
            pass


@gen.coroutine
def process_subreddit(subreddit, data_path='./data/pr0n/'):
    reddit = praw.Reddit(user_agent='gulperpr0n')
    submissions = skip_unfound(reddit.get_subreddit(subreddit).get_hot())
    for submission in submissions:
        try:
            url = normalize_url(submission.url)
            uid = unique_id(url)
        except ValueError:
            continue
        filepath = os.path.join(data_path, uid)
        if os.path.exists(filepath + '.pkl'):
            continue
        try:
            image_req = yield http_client.fetch(url, request_timeout=5)
        except HTTPError:
            continue
        image_fd = BytesIO(image_req.body)
        image = Image.open(image_fd)
        image_np = np.array(image)
        try:
            rects, scores, poses = detector.run(image_np)
        except RuntimeError:
            continue
        if len(scores) != 1:
            continue
        face_hash = openface.hash_face(image_np, bb=rects[0])
        print(subreddit, uid, url)
        data = {
            'url': url,
            'uid': uid,
            'rects': rects[0],
            'face_hash': face_hash,
            'reddit_submission': submission,
        }
        image.save(filepath + '.jpg')
        with open(filepath + '.pkl', 'wb+') as fd:
            pickle.dump(data, fd, protocol=-1)


@gen.coroutine
def process_subreddits():
    reddit = praw.Reddit(user_agent='gulperpr0n')
    with open('scripts/subreddits.txt') as fd:
        subreddits = list({s.strip() for s in fd})
    subreddits_done = set()
    while True:
        new_subreddits = set()
        while subreddits:
            todo, subreddits = subreddits[:10], subreddits[10:]
            print("[{}] Exploring subreddits: {}".
                  format(len(subreddits), ', '.join(todo)))
            yield [process_subreddit(s) for s in todo]
            for sub in todo:
                recommendations = {
                    rec.display_name
                    for rec in reddit.get_subreddit_recommendations(sub)
                }
                print("Recommendations for {}: {}".
                      format(sub, ', '.join(recommendations)))
                new_subreddits.update(recommendations)
            subreddits_done.update(todo)
        new_subreddits.difference_update(subreddits_done)
        subreddits = list(new_subreddits)
        with open('scripts/subreddits_done.txt', 'w+') as fd:
            for sub in subreddits_done:
                fd.write(sub + '\n')


if __name__ == "__main__":
    subreddits = "GentlemanBoners BeautifulFemales prettygirls attractivemen ".split()
    ioloop.IOLoop().instance().run_sync(process_subreddits)
