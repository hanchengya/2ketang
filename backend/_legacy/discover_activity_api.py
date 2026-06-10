#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性调研脚本: 摸清活动相关的源站 API,为新需求设计文档做准备。

目标:
  1. 活动列表接口能否像学生那样直接 API 调(提速可行性)
  2. 活动详情接口 + 字段(QQ群/地点/时间/院系/年级 等)
  3. 待开始活动的"报名名单"在哪个 tab / 接口 / 字段(重点找老师/角色标识)

用法(容器内): python /app/_legacy/discover_activity_api.py
"""
import sys
import json
import time

sys.path.insert(0, "/app")

from app.crawlers.login import login
from app.crawlers.student_crawler import _source_api_get
from selenium.webdriver.common.by import By

ACT_LIST_URL = "https://2ketangpc.svtcc.edu.cn/communist/activityDown?oto=0"
ACT_DETAIL_URL = "https://2ketangpc.svtcc.edu.cn/communist/activity/detail?id={}&oto=0&flag=1"

GRAB_JS = r"""
const staticExt = /\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|map)(\?|$)/i;
const out = performance.getEntriesByType('resource')
  .map(e => e.name)
  .filter(n => {
    try {
      const u = new URL(n, location.origin);
      return u.origin === location.origin
        && u.pathname.includes('/manage/server')
        && !staticExt.test(u.pathname);
    } catch(e){ return false; }
  });
return Array.from(new Set(out));
"""


def grab(driver):
    try:
        driver.execute_script("performance.clearResourceTimings();")
    except Exception:
        pass
    return []


def collect(driver):
    try:
        return driver.execute_script("return (function(){" + GRAB_JS + "})();") or []
    except Exception as e:
        print("  抓 URL 失败:", e)
        return []


def show(resp, label):
    print(f"\n  >>> {label}")
    if not resp:
        print("      调用失败/无返回")
        return
    data = resp.get("data")
    print(f"      status={resp.get('status')} url={resp.get('url')[:120]}")
    # 尽量找到列表体
    payload = data
    if isinstance(data, dict):
        print(f"      顶层 keys: {list(data.keys())}")
        for k in ("data", "rows", "list", "records", "result"):
            v = data.get(k)
            if isinstance(v, list) and v:
                payload = v
                break
            if isinstance(v, dict):
                for k2 in ("data", "rows", "list", "records"):
                    if isinstance(v.get(k2), list) and v.get(k2):
                        payload = v.get(k2)
                        break
    if isinstance(payload, list) and payload:
        print(f"      列表长度: {len(payload)}, 首条字段: {list(payload[0].keys())}")
        print(f"      首条样本: {json.dumps(payload[0], ensure_ascii=False)[:600]}")
    elif isinstance(payload, dict):
        print(f"      对象字段: {list(payload.keys())}")
        print(f"      样本: {json.dumps(payload, ensure_ascii=False)[:600]}")


def main():
    driver = login()
    if not driver:
        print("登录失败")
        return 1
    try:
        # ===== 1. 活动列表页(待开始 tab-5) =====
        print("\n" + "=" * 70)
        print("【1】活动列表页 - 待开始(tab-5)")
        print("=" * 70)
        driver.get(ACT_LIST_URL)
        time.sleep(6)
        grab(driver)
        try:
            driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "tab-5"))
        except Exception as e:
            print("点 tab-5 失败:", e)
        time.sleep(4)
        list_urls = collect(driver)
        print("活动列表接口候选:", list_urls)
        for u in list_urls:
            show(_source_api_get(driver, u, {"page": 1, "size": 20, "oto": 0}), f"列表调用 {u}")

        # 从 vue data 拿一个待开始活动 ID
        act_id = driver.execute_script(r"""
        function find(el){
          if(el.__vue__){var d=el.__vue__.$data||{};for(var k in d){var a=d[k];
            if(Array.isArray(a)&&a.length&&a[0]&&a[0].actId)return a[0].actId;}}
          for(var i=0;i<el.children.length;i++){var r=find(el.children[i]);if(r)return r;}
          return null;
        }
        return find(document.body);
        """)
        print("\n选中待开始活动 ID:", act_id)

        if act_id:
            # ===== 2. 活动详情页 =====
            print("\n" + "=" * 70)
            print(f"【2】活动详情页 act_id={act_id}")
            print("=" * 70)
            driver.get(ACT_DETAIL_URL.format(act_id))
            time.sleep(6)
            grab(driver)
            time.sleep(1)
            detail_urls = collect(driver)
            print("详情页接口候选:", detail_urls)
            for u in detail_urls:
                show(_source_api_get(driver, u, {"id": act_id, "actId": act_id, "oto": 0}),
                     f"详情调用 {u}")

            # ===== 3. 详情页所有 tab(找报名名单) =====
            print("\n" + "=" * 70)
            print("【3】详情页 tabs(找报名名单/签到名单)")
            print("=" * 70)
            tabs = driver.find_elements(By.CSS_SELECTOR, ".el-tabs__item")
            tab_info = [(t.get_attribute("id"), (t.text or "").strip()) for t in tabs]
            print("详情页 tabs:", tab_info)
            for tid, label in tab_info:
                if not tid:
                    continue
                try:
                    grab(driver)
                    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, tid))
                    time.sleep(3)
                    tab_urls = collect(driver)
                    print(f"\n--- tab {tid}({label}) 接口: {tab_urls}")
                    for u in tab_urls:
                        show(_source_api_get(driver, u, {"id": act_id, "actId": act_id, "page": 1, "size": 20}),
                             f"{label} 调用 {u}")
                except Exception as e:
                    print(f"  tab {tid}({label}) 失败: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
