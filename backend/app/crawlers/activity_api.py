#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动相关源站 API 封装(替代 Selenium 翻页,秒级)

接口(均 /manage/server):
  /activity/actAllList          活动列表(按 listType 分状态)
  /activity/member-personal     报名列表(含 role/identity 身份)
  /activity/member/info/all     签到签退名单(含 inTime/outTime)

认证走 source_api.source_api_get。Selenium 仅用于登录拿 sessionKey/cookie。
"""
from typing import Any, Dict, List, Tuple

from app.core.logging import get_logger
from app.crawlers.source_api import source_api_get

log = get_logger(__name__)

ACT_REFERER = "https://2ketangpc.svtcc.edu.cn/communist/activityDown?oto=0"

# listType → 状态名(与 selenium 版 tab 一致;数字即 tab-id 数字)
LIST_TYPE_STATUS = {
    2: "审核中",
    3: "被驳回",
    4: "报名中",
    5: "待开始",
    6: "进行中",
    7: "待完结",
    8: "完结审核中",
    9: "完结被驳回",
    0: "已完结",
}


def _records(resp) -> Tuple[List[Dict[str, Any]], int]:
    """从源站响应里取出列表体 + total。失败返回 ([], 0)。"""
    if not resp:
        return [], 0
    data = resp.get("data")
    if not isinstance(data, dict):
        return [], 0
    if str(data.get("code")) not in ("200", "0"):
        log.warning("接口业务错误 code=%s msg=%s", data.get("code"), data.get("msg"))
        return [], 0
    body = data.get("data")
    if isinstance(body, dict):
        for k in ("records", "list", "rows"):
            if isinstance(body.get(k), list):
                total = body.get("total") or body.get("totalCount") or len(body[k])
                return body[k], int(total)
        return [], 0
    if isinstance(body, list):
        return body, len(body)
    return [], 0


# ============ 活动列表 ============

def fetch_activity_page(driver, list_type: int, current: int, size: int) -> Tuple[List[Dict], int]:
    resp = source_api_get(driver, "/activity/actAllList", {
        "listType": list_type, "current": current, "size": size,
        "statTime": "", "endTime": "", "statusAcitive": str(list_type),
        "assistOrgId": "", "orgId": "", "actIdOrName": "", "calssId": "", "oto": "0",
    }, referer=ACT_REFERER)
    return _records(resp)


def fetch_all_activities(driver, list_type: int, page_size: int = 200, max_pages: int = 500) -> List[Dict]:
    """翻页拉完某状态的全部活动。"""
    out: List[Dict] = []
    seen = set()
    current = 1
    while current <= max_pages:
        records, total = fetch_activity_page(driver, list_type, current, page_size)
        if not records:
            break
        added = 0
        for r in records:
            aid = r.get("actId")
            if aid is not None and aid not in seen:
                seen.add(aid)
                out.append(r)
                added += 1
        if added == 0 or len(out) >= (total or 0):
            break
        current += 1
    return out


def crawl_all_activities_api(driver, list_types=None) -> Dict[str, List[Dict]]:
    """全状态全量爬取,返回 {状态名: [活动dict]},格式兼容 activity_repo.save_activities。"""
    targets = list_types if list_types is not None else list(LIST_TYPE_STATUS.keys())
    result: Dict[str, List[Dict]] = {}
    for lt in targets:
        name = LIST_TYPE_STATUS.get(lt, str(lt))
        acts = fetch_all_activities(driver, lt)
        result[name] = acts
        log.info("活动状态[%s] 拉取 %d 条", name, len(acts))
    return result


# ============ 报名列表 ============

def fetch_members(driver, act_id: int, page_size: int = 200, max_pages: int = 100) -> List[Dict]:
    """某活动的全部报名者(含 role/identity/code/name)。"""
    out: List[Dict] = []
    seen = set()
    current = 1
    while current <= max_pages:
        resp = source_api_get(driver, "/activity/member-personal", {
            "id": str(act_id), "current": current, "size": page_size,
            "status": "", "identity": "",
        }, referer=ACT_REFERER)
        records, total = _records(resp)
        if not records:
            break
        added = 0
        for r in records:
            key = r.get("code") or r.get("userId")
            if key is not None and key not in seen:
                seen.add(key)
                out.append(r)
                added += 1
        if added == 0 or len(out) >= (total or 0):
            break
        current += 1
    return out


# ============ 签到签退名单 ============

def fetch_sign_records(driver, act_id: int, page_size: int = 500, max_pages: int = 100) -> List[Dict]:
    """某活动签到签退名单(含 singIn/singOut/inTime/outTime/role)。"""
    out: List[Dict] = []
    seen = set()
    current = 1
    while current <= max_pages:
        resp = source_api_get(driver, "/activity/member/info/all", {
            "actId": str(act_id), "signIn": "", "signOut": "", "signType": "",
            "role": "", "shortMinute": "", "longtMinute": "", "keyWord": "",
            "current": current, "size": page_size, "total": 0, "iswork": "", "leave": "",
        }, referer=ACT_REFERER)
        records, total = _records(resp)
        if not records:
            break
        added = 0
        for r in records:
            key = r.get("code") or r.get("userId") or r.get("id")
            if key is not None and key not in seen:
                seen.add(key)
                out.append(r)
                added += 1
        if added == 0 or len(out) >= (total or 0):
            break
        current += 1
    return out
