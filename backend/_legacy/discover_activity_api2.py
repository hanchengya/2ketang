#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调研2: 用精确参数调活动接口,确认数据结构 + identity/role 取值。"""
import sys
import json
import time
from collections import Counter

sys.path.insert(0, "/app")
from app.crawlers.login import login
from app.crawlers.student_crawler import _source_api_get


def unwrap(resp):
    """取出列表体"""
    if not resp:
        return None, "无返回"
    data = resp.get("data")
    if not isinstance(data, dict):
        return None, f"data 非dict: {str(data)[:200]}"
    if data.get("code") not in ("200", 200, "0", 0):
        return None, f"业务错误 code={data.get('code')} msg={data.get('msg')}"
    body = data.get("data")
    # body 可能是 {records/list/rows:[...]} 或直接 list
    if isinstance(body, dict):
        for k in ("records", "list", "rows", "data"):
            if isinstance(body.get(k), list):
                return body.get(k), f"total={body.get('total') or body.get('totalCount')}"
        return [body], "单对象"
    if isinstance(body, list):
        return body, f"len={len(body)}"
    return None, f"body: {str(body)[:200]}"


def dump(rows, info, label, focus_fields=()):
    print(f"\n  >>> {label}  ({info})")
    if not rows:
        print("      空")
        return
    print(f"      首条字段: {list(rows[0].keys())}")
    print(f"      首条: {json.dumps(rows[0], ensure_ascii=False)[:700]}")
    for f in focus_fields:
        vals = Counter(str(r.get(f)) for r in rows)
        print(f"      字段 {f!r} 取值分布: {dict(vals)}")


def main():
    driver = login()
    if not driver:
        return 1
    try:
        # 1. 活动列表 - 待开始
        print("=" * 70)
        print("【1】actAllList 待开始(listType=5)")
        r = _source_api_get(driver, "/activity/actAllList", {
            "listType": 5, "current": 1, "size": 20, "statTime": "", "endTime": "",
            "statusAcitive": "5", "assistOrgId": "", "orgId": "", "actIdOrName": "",
            "calssId": "", "oto": "0"})
        rows, info = unwrap(r)
        dump(rows, info, "待开始活动列表")
        pending_id = rows[0].get("actId") if rows else None

        # 2. 活动列表 - 进行中
        print("\n" + "=" * 70)
        print("【2】actAllList 进行中(listType=6)")
        r = _source_api_get(driver, "/activity/actAllList", {
            "listType": 6, "current": 1, "size": 20, "statTime": "", "endTime": "",
            "statusAcitive": "6", "assistOrgId": "", "orgId": "", "actIdOrName": "",
            "calssId": "", "oto": "0"})
        rows2, info2 = unwrap(r)
        dump(rows2, info2, "进行中活动列表")
        ongoing_id = rows2[0].get("actId") if rows2 else None

        # 3. 报名列表(待开始活动) - 重点看 identity
        print("\n" + "=" * 70)
        print(f"【3】member-personal 报名列表 id={pending_id} (重点: identity 身份)")
        if pending_id:
            r = _source_api_get(driver, "/activity/member-personal", {
                "id": str(pending_id), "current": 1, "size": 50, "status": "", "identity": ""})
            rows, info = unwrap(r)
            dump(rows, info, "报名列表", focus_fields=("identity", "role", "isTeacher", "userType", "type"))

        # 4. 签到签退(进行中活动) - 重点看 role / signIn / signOut
        print("\n" + "=" * 70)
        print(f"【4】member/info/all 签到签退 actId={ongoing_id} (重点: role/signIn/signOut)")
        if ongoing_id:
            r = _source_api_get(driver, "/activity/member/info/all", {
                "actId": str(ongoing_id), "signIn": "", "signOut": "", "signType": "",
                "role": "", "shortMinute": "", "longtMinute": "", "keyWord": "",
                "current": 1, "size": 50, "total": 0, "iswork": "", "leave": ""})
            rows, info = unwrap(r)
            dump(rows, info, "签到签退名单", focus_fields=("role", "identity", "signIn", "signOut", "inTime", "outTime"))
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
