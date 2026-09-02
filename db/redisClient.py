# -*- coding: utf-8 -*-
"""
-----------------------------------------------------
   File Name：     redisClient.py
   Description :   封装Redis相关操作
   Author :        JHao
   date：          2019/8/9
------------------------------------------------------
   Change Activity:
                   2019/08/09: 封装Redis相关操作
                   2020/06/23: 优化pop方法, 改用hscan命令
                   2021/05/26: 区别http/https代理
------------------------------------------------------
"""
__author__ = 'JHao'

from redis.exceptions import TimeoutError, ConnectionError, ResponseError
from redis.connection import BlockingConnectionPool
from handler.logHandler import LogHandler
from handler.configHandler import ConfigHandler
from datetime import datetime
from random import choice
from redis import Redis
import json


class RedisClient(object):
    """
    Redis client

    Redis中代理存放的结构为hash：
    key为ip:port, value为代理属性的字典;

    """

    def __init__(self, **kwargs):
        """
        init
        :param host: host
        :param port: port
        :param password: password
        :param db: db
        :return:
        """
        self.name = ""
        kwargs.pop("username")
        self.__conn = Redis(connection_pool=BlockingConnectionPool(decode_responses=True,
                                                                   timeout=5,
                                                                   socket_timeout=5,
                                                                   protocol=2,
                                                                   **kwargs))

    def _filter_proxy(self, proxy_str, https=False, residential=None):
        try:
            data = json.loads(proxy_str)
            if https and not data.get("https"):
                return False
            if residential is True and not (data.get("is_residential") or data.get("residential")):
                return False
            if residential is False and (data.get("is_residential") or data.get("residential")):
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def _is_working(data):
        """ 最近一次校验是否通过 """
        status = data.get("last_status")
        return status is True or str(status).lower() == "true"

    @staticmethod
    def _check_age(data):
        """ 距上次校验的秒数; 无法解析时返回 None """
        last_time = data.get("last_time") or ""
        try:
            checked = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return None
        return (datetime.now() - checked).total_seconds()

    def _live_proxies(self, https=False, residential=None):
        """
        返回「最近校验通过」的代理列表, 按校验时间从新到旧排序。
        优先返回 PROXY_FRESH_SECONDS 秒内校验通过的代理;
        若无满足时效要求的, 退回到所有校验通过的代理, 避免空池。
        """
        max_age = ConfigHandler().proxyFreshSeconds
        working = []
        for proxy_str in self.__conn.hvals(self.name):
            if not self._filter_proxy(proxy_str, https=https, residential=residential):
                continue
            try:
                data = json.loads(proxy_str)
            except Exception:
                continue
            if not self._is_working(data):
                continue
            working.append((self._check_age(data), proxy_str))

        def _sort_key(item):
            age = item[0]
            return age if age is not None else float("inf")

        working.sort(key=_sort_key)
        if max_age and max_age > 0:
            fresh = [p for age, p in working if age is not None and age <= max_age]
            if fresh:
                return fresh
        return [p for _, p in working]

    def get(self, https=False, residential=None):
        """
        返回一个「最近校验通过」的代理
        :return:
        """
        proxies = self._live_proxies(https=https, residential=residential)
        return choice(proxies) if proxies else None

    def put(self, proxy_obj):
        """
        将代理放入hash, 使用changeTable指定hash name
        :param proxy_obj: Proxy obj
        :return:
        """
        data = self.__conn.hset(self.name, proxy_obj.proxy, proxy_obj.to_json)
        return data

    def pop(self, https=False, residential=None):
        """
        弹出一个代理
        :return: dict {proxy: value}
        """
        proxy = self.get(https=https, residential=residential)
        if proxy:
            self.__conn.hdel(self.name, json.loads(proxy).get("proxy", ""))
        return proxy if proxy else None

    def delete(self, proxy_str):
        """
        移除指定代理, 使用changeTable指定hash name
        :param proxy_str: proxy str
        :return:
        """
        return self.__conn.hdel(self.name, proxy_str)

    def exists(self, proxy_str):
        """
        判断指定代理是否存在, 使用changeTable指定hash name
        :param proxy_str: proxy str
        :return:
        """
        return self.__conn.hexists(self.name, proxy_str)

    def update(self, proxy_obj):
        """
        更新 proxy 属性
        :param proxy_obj:
        :return:
        """
        return self.__conn.hset(self.name, proxy_obj.proxy, proxy_obj.to_json)

    def getAll(self, https=False, residential=None, num=None, raw=False):
        """
        字典形式返回代理列表, 使用changeTable指定hash name。
        raw=False(默认): 只返回「最近校验通过」的代理, 校验时间从新到旧排序(供 /get /all 使用);
        raw=True: 返回池中全部代理(供调度器复检使用)。
        :return:
        """
        if raw:
            items = self.__conn.hvals(self.name)
            proxies = [x for x in items if self._filter_proxy(x, https=https, residential=residential)]
        else:
            proxies = self._live_proxies(https=https, residential=residential)
        if num is not None and isinstance(num, int) and num >= 0:
            proxies = proxies[:num]
        return proxies

    def clear(self):
        """
        清空所有代理, 使用changeTable指定hash name
        :return:
        """
        return self.__conn.delete(self.name)

    def getCount(self):
        """
        返回代理数量
        :return:
        """
        proxies = self.__conn.hvals(self.name)
        parsed = []
        for x in proxies:
            try:
                parsed.append(json.loads(x))
            except Exception:
                pass
        return {
            'total': len(parsed),
            'https': len([p for p in parsed if p.get("https")]),
            'residential': len([p for p in parsed if p.get("is_residential") or p.get("residential")])
        }


    def changeTable(self, name):
        """
        切换操作对象
        :param name:
        :return:
        """
        self.name = name

    def test(self):
        log = LogHandler('redis_client')
        try:
            self.getCount()
        except TimeoutError as e:
            log.error('redis connection time out: %s' % str(e), exc_info=True)
            return e
        except ConnectionError as e:
            log.error('redis connection error: %s' % str(e), exc_info=True)
            return e
        except ResponseError as e:
            log.error('redis connection error: %s' % str(e), exc_info=True)
            return e


