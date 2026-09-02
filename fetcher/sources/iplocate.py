# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     iplocate.py
   Description :   IPLocate free-proxy-list 代理源
   Author :        JHao
   date：          2026/09/03
-------------------------------------------------
   Change Activity:
                   2026/09/03: 新增 iplocate 源
-------------------------------------------------
"""
__author__ = 'JHao'

from fetcher.baseFetcher import BaseFetcher
from handler.logHandler import LogHandler
from util.webRequest import WebRequest

logger = LogHandler("fetcher")


class IPLocateFetcher(BaseFetcher):
    """IPLocate free-proxy-list https://github.com/iplocate/free-proxy-list"""

    name = "iplocate"
    url = "https://github.com/iplocate/free-proxy-list"

    enabled = True

    def fetch(self):
        # 该列表每行形如 "http://ip:port" / "socks5://ip:port"
        # 代理池内部统一按 http 代理处理, 故仅采集 http/https 行, socks 行跳过
        raw_url = ("https://github.com/iplocate/free-proxy-list/"
                   "raw/refs/heads/main/all-proxies.txt")
        try:
            r = WebRequest().get(raw_url, timeout=10)
        except Exception as e:
            logger.error("ProxyFetch - iplocate: %s" % e)
            return
        proxies = []
        for line in r.text.splitlines():
            line = line.strip()
            if not line or "://" not in line:
                continue
            scheme, addr = line.split("://", 1)
            if scheme.lower() not in ("http", "https"):
                continue
            proxies.extend(self.parseProxiesFromText(addr))
        for proxy in self.yieldUniqueProxies(proxies):
            yield proxy


if __name__ == '__main__':
    for proxy in IPLocateFetcher().fetch():
        print(proxy)
