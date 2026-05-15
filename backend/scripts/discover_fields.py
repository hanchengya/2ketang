#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探测 tab-1 (全部) 里活动对象的字段, 重点看 finishStatus 是否随每条记录返回。
如果是, 改成只爬 tab-1 就能拿全活动 + 真实状态。

用法 (容器里):
    python /app/scripts/discover_fields.py
"""
import sys
import time
import json

sys.path.insert(0, "/app")

from app.crawlers.login import login
from selenium.webdriver.common.by import By

URL = "https://2ketangpc.svtcc.edu.cn/communist/activityDown?oto=0"


def find_activity_array(driver):
    """从 vue $data 里找最大的、看起来像活动的数组。"""
    script = """
    function looksLikeActivity(item) {
        if (!item || typeof item !== 'object') return false;
        return !!(item.actId || item.act_id);
    }
    function collect(el, out) {
        if (el.__vue__) {
            var data = el.__vue__.$data || {};
            for (var k in data) {
                var arr = data[k];
                if (Array.isArray(arr) && arr.length > 0 && looksLikeActivity(arr[0])) {
                    out.push({key: k, arr: arr, len: arr.length});
                }
            }
        }
        for (var i = 0; i < el.children.length; i++) {
            collect(el.children[i], out);
        }
    }
    var out = [];
    collect(document.body, out);
    if (out.length === 0) return null;
    out.sort(function(a, b){ return b.len - a.len; });
    var top = out[0];
    return {
        key: top.key,
        len: top.len,
        samples: top.arr.slice(0, 3),
        // 把每条的 finishStatus 都汇总
        finishStatusValues: top.arr.map(function(x){ return x.finishStatus || null; })
    };
    """
    return driver.execute_script(script)


def click_tab(driver, tid):
    el = driver.find_element(By.ID, tid)
    driver.execute_script("arguments[0].click();", el)
    time.sleep(3)


def main():
    driver = login()
    if not driver:
        print("登录失败")
        return 1

    try:
        driver.get(URL)
        time.sleep(6)

        for tid, label in [("tab-1", "全部"), ("tab-6", "进行中"), ("tab-0", "已完结")]:
            print(f"\n========== {tid} ({label}) ==========")
            click_tab(driver, tid)
            time.sleep(2)
            info = find_activity_array(driver)
            if not info:
                print("  未找到活动数组")
                continue

            first = info["samples"][0]
            keys = list(first.keys())
            print(f"  数组 len={info['len']}, 字段 ({len(keys)}): {keys}")
            print(f"  第 1 条 finishStatus = {first.get('finishStatus')!r}")
            print(f"  第 1 条 finishStatus2 = {first.get('finishStatus2')!r}")
            print(f"  第 1 条 status = {first.get('status')!r}, statusAll = {first.get('statusAll')!r}")
            print(f"  第 1 条 name = {first.get('name')!r}")

            # finishStatus 值分布
            fs_values = info["finishStatusValues"]
            from collections import Counter
            dist = Counter([v if v is not None else "(空)" for v in fs_values])
            print(f"  本 tab 内 finishStatus 值分布:")
            for k, v in dist.most_common():
                print(f"    {k!r}: {v}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
