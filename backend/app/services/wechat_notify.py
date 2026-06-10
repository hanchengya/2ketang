#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信订阅消息 - 业务通知组装层

把"活动 + 场景"翻译成具体订阅消息模板的 data,再交给 wechat_service 下发。
负责处理:
  - thing 字段 ≤20 字截断(超长微信报 47003)
  - phrase 字段 ≤5 字截断
  - time 字段格式化(datetime → "YYYY-MM-DD HH:MM")
  - 按场景选模板 + 组 data

场景(scene)与模板:
  enrollable  可报名     → 模板 C(ENROLL)   发给有权限的学生
  enrolled    报名成功   → 模板 A(ACTIVITY) 发给报名者
  sign_in     请签到     → 模板 A(ACTIVITY)
  sign_out    请签退     → 模板 A(ACTIVITY)
  admin       管理员通知 → 模板 B(REVIEW)
"""
from datetime import datetime
from typing import Any, Dict, Optional

from app.config import settings
from app.core.logging import get_logger
from app.services import wechat_service

log = get_logger(__name__)

# 点击通知跳转的小程序页面
_DETAIL_PAGE = "pages/activity/detail/detail"


# ============ 字段处理 ============

def _thing(s: Any, limit: int = 20) -> str:
    """thing 字段: 截断到 limit 字符(微信 thing 上限 20)。空值给占位。"""
    s = str(s or "").strip()
    if not s:
        return "无"
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _phrase(s: Any, limit: int = 5) -> str:
    """phrase 字段: ≤5 个汉字。"""
    s = str(s or "").strip()
    return s[:limit] if len(s) > limit else (s or "无")


def _time(dt: Any) -> str:
    """time 字段: datetime/字符串 → 'YYYY-MM-DD HH:MM'。空给占位。"""
    if not dt:
        return "待定"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    # 字符串: 取前 16 位(YYYY-MM-DD HH:MM),容忍 ISO 带 T
    s = str(dt).replace("T", " ")
    return s[:16] if len(s) >= 16 else s


def _page(act_id: Any) -> str:
    return f"{_DETAIL_PAGE}?id={act_id}" if act_id else _DETAIL_PAGE


# ============ 各场景 data 组装 ============

def _data_activity(activity: Dict[str, Any], thing5_text: str) -> Dict[str, Dict[str, str]]:
    """模板 A 活动参与通知: thing1 活动名/time2 发起时间/thing4 地址/thing5 活动对象

    time2 用"通知发起的当前时间"(而非活动开始时间),签到/签退/报名成功
    都体现"刚刚提醒你"的即时感。容器时区 Asia/Shanghai,now() 即北京时间。
    """
    return {
        "thing1": {"value": _thing(activity.get("name") or activity.get("act_name"))},
        "time2": {"value": _time(datetime.now())},
        "thing4": {"value": _thing(activity.get("pitch_address") or "见活动详情")},
        "thing5": {"value": _thing(thing5_text)},
    }


def _data_enroll(activity: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """模板 C 报名时间提醒: thing9 活动名/time6 开始/time7 截止/thing3 温馨提示"""
    return {
        "thing9": {"value": _thing(activity.get("name") or activity.get("act_name"))},
        "time6": {"value": _time(activity.get("start_time"))},
        "time7": {"value": _time(activity.get("enroll_end_time"))},
        "thing3": {"value": _thing("你符合条件,可以报名啦")},
    }


def _data_review(activity: Dict[str, Any], result_text: str, note: str = "") -> Dict[str, Dict[str, str]]:
    """模板 B 审核通过通知: thing15 任务名/thing5 备注/phrase1 审核结果"""
    return {
        "thing15": {"value": _thing(activity.get("name") or activity.get("act_name"))},
        "thing5": {"value": _thing(note or "请及时处理")},
        "phrase1": {"value": _phrase(result_text)},
    }


# scene → (template_id getter, data builder)
def _build(scene: str, activity: Dict[str, Any]):
    if scene == "enrollable":
        return settings.WECHAT_TMPL_ENROLL, _data_enroll(activity)
    if scene == "enrolled":
        return settings.WECHAT_TMPL_ACTIVITY, _data_activity(activity, "报名成功")
    if scene == "sign_in":
        return settings.WECHAT_TMPL_ACTIVITY, _data_activity(activity, "请及时签到")
    if scene == "sign_out":
        return settings.WECHAT_TMPL_ACTIVITY, _data_activity(activity, "请及时签退")
    raise ValueError(f"未知通知场景: {scene}")


# ============ 对外接口 ============

def notify(openid: str, scene: str, activity: Dict[str, Any]) -> Dict[str, Any]:
    """给单个 openid 发一条活动相关订阅消息。

    Args:
        openid: 接收者 openid
        scene: enrollable / enrolled / sign_in / sign_out
        activity: 活动 dict(含 name/act_name, start_time, enroll_end_time, pitch_address, act_id)

    Returns:
        微信返回 dict(errcode/errmsg)。失败不抛异常,记录日志并返回结果给调用方判断。
    """
    template_id, data = _build(scene, activity)
    act_id = activity.get("act_id") or activity.get("actId")
    try:
        result = wechat_service.send_subscribe_message(
            touser=openid,
            template_id=template_id,
            data=data,
            page=_page(act_id),
        )
        if result.get("errcode", 0) != 0:
            log.warning("订阅消息下发失败 scene=%s openid=%s result=%s", scene, openid, result)
        return result
    except Exception as e:
        log.exception("订阅消息异常 scene=%s openid=%s", scene, openid)
        return {"errcode": -1, "errmsg": str(e)}


def notify_admin(openid: str, activity: Dict[str, Any], result_text: str, note: str = "") -> Dict[str, Any]:
    """给管理员/老师发审核类通知(模板 B)。"""
    act_id = activity.get("act_id") or activity.get("actId")
    try:
        result = wechat_service.send_subscribe_message(
            touser=openid,
            template_id=settings.WECHAT_TMPL_REVIEW,
            data=_data_review(activity, result_text, note),
            page=_page(act_id),
        )
        if result.get("errcode", 0) != 0:
            log.warning("管理员通知下发失败 openid=%s result=%s", openid, result)
        return result
    except Exception as e:
        log.exception("管理员通知异常 openid=%s", openid)
        return {"errcode": -1, "errmsg": str(e)}
