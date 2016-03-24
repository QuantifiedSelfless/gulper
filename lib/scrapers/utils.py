from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
import ujson as json


http_client = AsyncHTTPClient()


def apiclient_paginate(resource, action, params, http=None, max_results=500):
    request = getattr(resource, action)(**params)
    num_results = 0
    while request is not None and num_results < max_results:
        data = request.execute(http=http)
        try:
            items = data['items']
        except KeyError:
            items = data['files']
        num_results += len(items)
        yield from items
        request = resource.list_next(request, data)

@gen.coroutine
def facebook_paginate(data, max_results=500):
    paginated_data = []
    while True:
        paginated_data.extend(data['data'])
        if max_results is not None and len(paginated_data) >= max_results:
            break
        try:
            paginate_url = data['paging']['next']
        except KeyError:
            break
        try:
            request = yield http_client.fetch(paginate_url)
        except HTTPError as e:
            print("Exception while paginating facebook request: ", e)
            break
        data = json.loads(request.body)
    return paginated_data
