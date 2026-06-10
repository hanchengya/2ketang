#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
签到 / 签退 通知服务

对"进行中"的活动:
  1. 拉签到名单 fetch_sign_records(act_id)
  2. 数 singIn==1 / singOut==1 的人数
  3. 达阈值(默认 SIGN_NOTIFY_THRESHOLD)且本活动该类型还没发过 → 给全体报名者发"请签到/签退"
  4. 防重复: activity_notifications(act_id, sign_in/sign_out) 每活动每类型只发一次

发送对象(从签到名单按 identity 分):
  identity==1 学生 → openid(student 绑定) → wechat_notify.notify(scene)
  identity==2 老师/组织 → openid(admin 绑定) → wechat_notify.notify_admin

只有"绑定学号 + 授权过模板"的人能真正收到(微信订阅消息机制)。
"""
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import get_logger
from app.crawlers.activity_api import fetch_sign_records
from app.models import Activity, ActivityDetail, ActivityNotification
from app.repositories import binding_repo
from app.services import wechat_notify

log = get_logger(__name__)


def _already_sent(db: Session, act_id: int, ntype: str) -> bool:
    return db.query(ActivityNotification).filter(
        ActivityNotification.act_id == act_id,
        ActivityNotification.notification_type == ntype,
    ).first() is not None


def _mark_sent(db: Session, act_id: int, ntype: str, recipient: int, success: int, fail: int) -> None:
    db.add(ActivityNotification(
        act_id=act_id,
        notification_type=ntype,
        sent_at=datetime.now(),
        recipient_count=recipient,
        success_count=success,
        fail_count=fail,
    ))
    db.commit()


def _activity_payload(db: Session, act: Activity) -> Dict[str, Any]:
    """组装给 wechat_notify 的活动 dict(name/start_time/pitch_address...)。"""
    detail = db.query(ActivityDetail).filter(ActivityDetail.act_id == act.act_id).first()
    return {
        "name": act.name,
        "act_id": act.act_id,
        "start_time": act.start_time,
        "enroll_end_time": act.enroll_end_time,
        "pitch_address": detail.pitch_address if detail else None,
    }


def _send_one(db: Session, act: Activity, records: List[Dict], scene: str) -> Dict[str, int]:
    """给一个活动的全体报名者发 scene 通知。返回 {recipient, success, fail}。"""
    payload = _activity_payload(db, act)
    recipient = success = fail = 0
    admin_result = "待签到" if scene == "sign_in" else "待签退"

    for r in records:
        code = str(r.get("code") or "").strip()
        if not code:
            continue
        identity = r.get("identity")

        if identity == 2:
            # 老师 / 组织账号 → 绑定 admin 的人,模板 B
            for oid in binding_repo.openids_by_code(db, code, "admin"):
                recipient += 1
                res = wechat_notify.notify_admin(oid, payload, admin_result, note="请关注活动签到")
                success += 1 if res.get("errcode") == 0 else 0
                fail += 0 if res.get("errcode") == 0 else 1
        else:
            # 学生(identity==1 或其它)→ 绑定 student 的人,模板 A
            for oid in binding_repo.openids_by_code(db, code, "student"):
                recipient += 1
                res = wechat_notify.notify(oid, scene, payload)
                success += 1 if res.get("errcode") == 0 else 0
                fail += 0 if res.get("errcode") == 0 else 1

    return {"recipient": recipient, "success": success, "fail": fail}


def run_sign_notify(
    db: Session,
    driver,
    threshold: Optional[int] = None,
    act_ids: Optional[List[int]] = None,
    stop_check: Optional[Callable[[], bool]] = None,
    log_fn: Callable[[str], None] = lambda m: None,
) -> Dict[str, int]:
    """检查并发送签到/签退通知。

    Args:
        driver: 已登录的 selenium driver(fetch_sign_records 需要登录态)
        threshold: 触发阈值,默认 settings.SIGN_NOTIFY_THRESHOLD
        act_ids: 指定活动;None 则取所有"进行中"活动
    Returns:
        汇总统计
    """
    th = threshold if threshold is not None else settings.SIGN_NOTIFY_THRESHOLD

    if act_ids:
        acts = db.query(Activity).filter(Activity.act_id.in_(act_ids)).all()
    else:
        acts = db.query(Activity).filter(Activity.finish_status == "进行中").all()

    summary = {"checked": 0, "sign_in_sent": 0, "sign_out_sent": 0,
               "msg_success": 0, "msg_fail": 0}
    log_fn(f"待检查活动 {len(acts)} 个,阈值 {th}")

    for act in acts:
        if stop_check and stop_check():
            log_fn("收到停止信号")
            break

        try:
            records = fetch_sign_records(driver, act.act_id)
        except Exception:
            log.exception("拉签到名单失败 act_id=%s", act.act_id)
            continue

        summary["checked"] += 1
        signin_n = sum(1 for r in records if r.get("singIn") == 1)
        signout_n = sum(1 for r in records if r.get("singOut") == 1)

        # 签到
        if signin_n >= th and not _already_sent(db, act.act_id, "sign_in"):
            res = _send_one(db, act, records, "sign_in")
            _mark_sent(db, act.act_id, "sign_in", res["recipient"], res["success"], res["fail"])
            summary["sign_in_sent"] += 1
            summary["msg_success"] += res["success"]
            summary["msg_fail"] += res["fail"]
            log_fn(f"[{act.act_id}] 签到通知: 已签到 {signin_n} 人 → 触达 {res['recipient']} (成功 {res['success']})")

        # 签退
        if signout_n >= th and not _already_sent(db, act.act_id, "sign_out"):
            res = _send_one(db, act, records, "sign_out")
            _mark_sent(db, act.act_id, "sign_out", res["recipient"], res["success"], res["fail"])
            summary["sign_out_sent"] += 1
            summary["msg_success"] += res["success"]
            summary["msg_fail"] += res["fail"]
            log_fn(f"[{act.act_id}] 签退通知: 已签退 {signout_n} 人 → 触达 {res['recipient']} (成功 {res['success']})")

    log_fn(f"完成: 检查 {summary['checked']} 活动, "
           f"签到通知 {summary['sign_in_sent']} / 签退通知 {summary['sign_out_sent']}, "
           f"消息成功 {summary['msg_success']} 失败 {summary['msg_fail']}")
    return summary
