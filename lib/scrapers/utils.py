from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
import ujson as json
import re


http_client = AsyncHTTPClient()

ssn = re.compile("(\d{3}-?\d{2}-?\d{4}|XXX-XX-XXXX)$")
ccn = re.compile("(?:\d[ -]*?){13,16}")
phone = re.compile("(\d{3}-?\d{3}-?\d{4}|XXX-XXX-XXXX)$")

def filter_text(text_str):
    t1 = re.search(ssn, text_str)
    t2 = re.search(ccn, text_str)
    t3 = re.search(phone, text_str)
    if t1 == None and t2 == None and t3 == None:
        return True
    else
        return False


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
