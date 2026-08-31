# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File Name：     ProxyApi.py
   Description :   WebApi
   Author :       JHao
   date：          2016/12/4
-------------------------------------------------
   Change Activity:
                   2016/12/04: WebApi
                   2019/08/14: 集成Gunicorn启动方式
                   2020/06/23: 新增pop接口
                   2022/07/21: 更新count接口
-------------------------------------------------
"""
__author__ = 'JHao'

import logging
import platform
from werkzeug.wrappers import Response
from flask import Flask, jsonify, request

from util.six import iteritems
from helper.proxy import Proxy
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler

# Suppress requestor IP logging from werkzeug logger to ensure zero-log requestor privacy
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
conf = ConfigHandler()
proxy_handler = ProxyHandler()


class JsonResponse(Response):
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response, (dict, list)):
            response = jsonify(response)

        return super(JsonResponse, cls).force_type(response, environ)


app.response_class = JsonResponse

api_list = [
    {"url": "/get", "params": "type: 'https'|'', residential: 'true'|'false'", "desc": "get a proxy"},
    {"url": "/pop", "params": "type: 'https'|'', residential: 'true'|'false'", "desc": "get and delete a proxy"},
    {"url": "/delete", "params": "proxy: 'e.g. 127.0.0.1:8080'", "desc": "delete an unusable proxy"},
    {"url": "/all", "params": "type: 'https'|'', residential: 'true'|'false', num: 'int'", "desc": "get all proxies from proxy pool"},
    {"url": "/count", "params": "", "desc": "return proxy count statistics"}
]


@app.before_request
def verify_token():
    auth_token = conf.authToken
    if not auth_token:
        return None

    auth_header = request.headers.get("Authorization", "")
    req_token = None
    if auth_header.startswith("Bearer "):
        req_token = auth_header[7:].strip()
    elif auth_header.startswith("Token "):
        req_token = auth_header[6:].strip()
    elif auth_header:
        req_token = auth_header.strip()

    if not req_token:
        req_token = (
            request.headers.get("X-API-Token")
            or request.headers.get("X-Auth-Token")
            or request.headers.get("Api-Key")
            or request.args.get("token")
            or request.args.get("api_key")
        )

    if req_token != auth_token:
        return jsonify({"code": 401, "src": "Unauthorized: invalid or missing token"}), 401


def _parse_params():
    req_type = request.args.get("type", "").lower()
    https = (req_type == 'https')
    res_arg = request.args.get("residential", "").lower() or request.args.get("is_residential", "").lower()
    if res_arg in ["true", "1", "yes"] or req_type == "residential":
        residential = True
    elif res_arg in ["false", "0", "no"]:
        residential = False
    else:
        residential = None

    num_arg = request.args.get("num") or request.args.get("count")
    num = None
    if num_arg is not None:
        try:
            num = int(num_arg)
        except ValueError:
            num = None

    return https, residential, num


@app.route('/')
def index():
    return {'url': api_list}


@app.route('/get/')
def get():
    https, residential, _ = _parse_params()
    proxy = proxy_handler.get(https=https, residential=residential)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}


@app.route('/pop/')
def pop():
    https, residential, _ = _parse_params()
    proxy = proxy_handler.pop(https=https, residential=residential)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}


@app.route('/refresh/')
def refresh():
    # TODO refresh会有守护程序定时执行，由api直接调用性能较差，暂不使用
    return 'success'


@app.route('/all/')
def getAll():
    https, residential, num = _parse_params()
    proxies = proxy_handler.getAll(https=https, residential=residential, num=num)
    return jsonify([_.to_dict for _ in proxies])


@app.route('/delete/', methods=['GET'])
def delete():
    proxy = request.args.get('proxy')
    status = proxy_handler.delete(Proxy(proxy))
    return {"code": 0, "src": status}


@app.route('/count/')
def getCount():
    proxies = proxy_handler.getAll()
    http_type_dict = {}
    source_dict = {}
    residential_count = 0
    for proxy in proxies:
        http_type = 'https' if proxy.https else 'http'
        http_type_dict[http_type] = http_type_dict.get(http_type, 0) + 1
        if proxy.is_residential:
            residential_count += 1
        for source in proxy.source.split('/'):
            if source:
                source_dict[source] = source_dict.get(source, 0) + 1
    return {
        "http_type": http_type_dict,
        "residential": residential_count,
        "source": source_dict,
        "count": len(proxies)
    }


def runFlask():
    if platform.system() == "Windows":
        app.run(host=conf.serverHost, port=conf.serverPort)
    else:
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):

            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super(StandaloneApplication, self).__init__()

            def load_config(self):
                _config = dict([(key, value) for key, value in iteritems(self.options)
                                if key in self.cfg.settings and value is not None])
                for key, value in iteritems(_config):
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        _options = {
            'bind': '%s:%s' % (conf.serverHost, conf.serverPort),
            'workers': conf.gunicornWorkers,
            'threads': conf.gunicornThreads,
            'accesslog': None,  # Disable accesslog to enforce requestor privacy (zero logs)
            'max_requests': 1000,
            'max_requests_jitter': 50,
            'timeout': 60
        }
        StandaloneApplication(app, _options).run()


if __name__ == '__main__':
    runFlask()

