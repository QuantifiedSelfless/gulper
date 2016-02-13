from tornado import web
import json
import time


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class BaseHandler(web.RequestHandler):
    def api_response(self, data, code=200, reason=None):
        self.set_header("Content-Type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        self.write(json.dumps({
            "status_code": code,
            "timestamp": time.time(),
            "data": data,
        }, cls=JSONEncoder))
        self.set_status(code, reason)
        self.finish()

    def error(self, code, reason=None, body=None):
        self.add_header("Access-Control-Allow-Origin", "*")
        if body:
            self.write(body)
        self.set_status(code, reason)
        self.finish()

    def get_secure_cookie(self, *args, **kwargs):
        result = super().get_secure_cookie(*args, **kwargs)
        return result.decode()

