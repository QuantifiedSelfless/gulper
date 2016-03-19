

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
