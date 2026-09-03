# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     configHandler
   Description :
   Author :        JHao
   date：          2020/6/22
-------------------------------------------------
   Change Activity:
                   2020/6/22:
-------------------------------------------------
"""
__author__ = 'JHao'

import os
import setting
from util.singleton import Singleton
from util.lazyProperty import LazyProperty
from util.six import reload_six, withMetaclass


class ConfigHandler(withMetaclass(Singleton)):

    def __init__(self):
        pass

    @LazyProperty
    def serverHost(self):
        return os.environ.get("HOST", setting.HOST)

    @LazyProperty
    def serverPort(self):
        return os.environ.get("PORT", setting.PORT)

    @LazyProperty
    def authToken(self):
        return os.getenv("AUTH_TOKEN", getattr(setting, "AUTH_TOKEN", ""))

    @LazyProperty
    def sslEnabled(self):
        val = os.getenv("SSL_ENABLED", getattr(setting, "SSL_ENABLED", False))
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ("1", "true", "yes", "on")

    @LazyProperty
    def sslCertFile(self):
        return self._resolvePath(os.getenv("SSL_CERTFILE", getattr(setting, "SSL_CERTFILE", "gateway/tls.crt")))

    @LazyProperty
    def sslKeyFile(self):
        return self._resolvePath(os.getenv("SSL_KEYFILE", getattr(setting, "SSL_KEYFILE", "gateway/tls.key")))

    @staticmethod
    def _resolvePath(path):
        if not path or os.path.isabs(path):
            return path
        root = os.path.dirname(os.path.abspath(setting.__file__))
        return os.path.join(root, path)

    @LazyProperty
    def gunicornWorkers(self):
        return int(os.getenv("GUNICORN_WORKERS", getattr(setting, "GUNICORN_WORKERS", 2)))

    @LazyProperty
    def gunicornThreads(self):
        return int(os.getenv("GUNICORN_THREADS", getattr(setting, "GUNICORN_THREADS", 2)))

    @LazyProperty
    def logLevel(self):
        return os.getenv("LOG_LEVEL", getattr(setting, "LOG_LEVEL", "INFO"))

    @LazyProperty
    def dbConn(self):
        return os.getenv("DB_CONN", setting.DB_CONN)

    @LazyProperty
    def tableName(self):
        return os.getenv("TABLE_NAME", setting.TABLE_NAME)

    @property
    def fetcherExclude(self):
        reload_six(setting)
        return getattr(setting, 'PROXY_FETCHER_EXCLUDE', [])

    @LazyProperty
    def httpUrl(self):
        return os.getenv("HTTP_URL", setting.HTTP_URL)

    @LazyProperty
    def httpsUrl(self):
        return os.getenv("HTTPS_URL", setting.HTTPS_URL)

    @LazyProperty
    def verifyTimeout(self):
        return int(os.getenv("VERIFY_TIMEOUT", setting.VERIFY_TIMEOUT))

    # @LazyProperty
    # def proxyCheckCount(self):
    #     return int(os.getenv("PROXY_CHECK_COUNT", setting.PROXY_CHECK_COUNT))

    @LazyProperty
    def maxFailCount(self):
        return int(os.getenv("MAX_FAIL_COUNT", setting.MAX_FAIL_COUNT))

    # @LazyProperty
    # def maxFailRate(self):
    #     return int(os.getenv("MAX_FAIL_RATE", setting.MAX_FAIL_RATE))

    @LazyProperty
    def poolSizeMin(self):
        return int(os.getenv("POOL_SIZE_MIN", setting.POOL_SIZE_MIN))

    @LazyProperty
    def proxyFreshSeconds(self):
        return int(os.getenv("PROXY_FRESH_SECONDS", getattr(setting, "PROXY_FRESH_SECONDS", 900)))

    @LazyProperty
    def proxyRegion(self):
        return bool(os.getenv("PROXY_REGION", setting.PROXY_REGION))

    @LazyProperty
    def timezone(self):
        return os.getenv("TIMEZONE", setting.TIMEZONE)

