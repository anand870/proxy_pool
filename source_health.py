# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     source_health.py
   Description :   逐个运行 fetcher/sources/ 下的代理源，实时校验其产出的代理，
                   统计每个源「抓到多少 / 可用多少 / 可用率」以及哪些源已失效。
                   不依赖数据库，不修改任何业务代码。
   Author :        analysis tool
-------------------------------------------------
   用法:
       python source_health.py                # 跑全部源
       python source_health.py scdn ip89      # 只跑指定源
       python source_health.py --no-validate  # 只抓取不校验(快)
-------------------------------------------------
"""
import os
import sys
import time
import json
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from helper.fetch import _discover_fetchers          # noqa: E402
from helper.proxy import Proxy                        # noqa: E402
from helper.check import DoValidator                  # noqa: E402

MAX_WORKERS = 50


def collect(only=None):
    """运行每个源的 fetch()，返回 {source_name: set(proxy_str)} 与耗时/错误信息"""
    src_map = {}
    meta = {}
    for fc in _discover_fetchers([]):
        if only and fc.name not in only:
            continue
        got = set()
        err = ""
        t0 = time.time()
        try:
            for item in fc().fetch():
                s = item.proxy if hasattr(item, "proxy") else (
                    item[0] if isinstance(item, tuple) else str(item))
                got.add(s.strip())
        except Exception as e:  # noqa: BLE001
            err = repr(e)
        src_map[fc.name] = got
        meta[fc.name] = (round(time.time() - t0, 1), err)
        flag = "OK   " if got else ("ERR  " if err else "EMPTY")
        print("fetch  %-14s %s %4d  %5.1fs  %s"
              % (fc.name, flag, len(got), meta[fc.name][0], err[:70]))
    return src_map, meta


def validate(proxies):
    """并发校验，返回 {proxy_str: (http_ok, https_ok)}"""
    def _check(p):
        pr = Proxy(p)
        try:
            pr = DoValidator.validator(pr, "use")
            return p, bool(pr.last_status), bool(pr.https)
        except Exception:  # noqa: BLE001
            return p, False, False

    out = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for p, ok, https in ex.map(_check, list(proxies)):
            out[p] = (ok, https)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    do_validate = "--no-validate" not in sys.argv
    only = set(args) or None

    src_map, meta = collect(only)

    all_proxies = {}
    for name, ps in src_map.items():
        for p in ps:
            all_proxies.setdefault(p, []).append(name)
    print("\nunique proxies: %d" % len(all_proxies))

    res = {}
    if do_validate and all_proxies:
        t0 = time.time()
        res = validate(all_proxies.keys())
        print("validation took %.0fs\n" % (time.time() - t0))

    print("%-14s %7s %7s %6s %8s   %s"
          % ("source", "fetched", "working", "rate", "https_ok", "note"))
    print("-" * 70)
    rows = []
    for name, ps in src_map.items():
        tot = len(ps)
        work = sum(1 for p in ps if res.get(p, (False, False))[0])
        https = sum(1 for p in ps if res.get(p, (False, False))[1])
        rate = (work / tot * 100) if tot else 0.0
        note = meta[name][1][:40] if meta[name][1] else (
            "" if tot else "no proxies returned")
        rows.append((name, tot, work, rate, https, note))

    for name, tot, work, rate, https, note in sorted(rows, key=lambda r: -r[2]):
        print("%-14s %7d %7d %5.0f%% %8d   %s"
              % (name, tot, work, rate, https, note))

    if res:
        tot_all = len(all_proxies)
        work_all = sum(1 for v in res.values() if v[0])
        print("-" * 70)
        print("%-14s %7d %7d %5.0f%%"
              % ("TOTAL (uniq)", tot_all, work_all,
                 work_all / tot_all * 100 if tot_all else 0))

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join("log", "source_health_%s.json" % stamp)
    try:
        json.dump(
            {"generated": stamp,
             "fetched": {k: sorted(v) for k, v in src_map.items()},
             "meta": meta,
             "validation": res},
            open(out_path, "w"), indent=2)
        print("\nraw result -> %s" % out_path)
    except Exception as e:  # noqa: BLE001
        print("could not write json: %s" % e)


if __name__ == "__main__":
    main()
