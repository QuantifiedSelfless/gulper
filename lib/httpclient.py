from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
import logging


FORMAT = '[%(levelname)1.1s %(asctime)s %(name)s:%(lineno)d] %(message)s'
logger = logging.getLogger("httpclient")

http_client = AsyncHTTPClient()


@gen.coroutine
def fetch(url, *args, **kwargs):
    retry_max = kwargs.pop('retry_max', 5)
    retry = 0
    while True:
        try:
            result = yield http_client.fetch(url, *args, **kwargs)
            return result
        except HTTPError as e:
            if e.code == 599:
                retry += 1
                if retry < retry_max:
                    logger.error(
                        "Timeout in request: "
                        "sleeping for {}: {}".format(2**retry, url)
                    )
                    yield gen.sleep(2**retry)
                    continue
            raise
