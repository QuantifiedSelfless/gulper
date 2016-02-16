

def apiclient_paginate(resource, action, params, http=None, max_results=500):
    params['maxResults'] = 50
    request = getattr(resource, action)(**params)
    num_results = 0
    while request is not None and num_results < max_results:
        data = request.execute(http=http)
        num_results += len(data['items'])
        yield from data['items']
        request = resource.list_next(request, data)
