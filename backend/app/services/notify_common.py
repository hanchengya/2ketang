#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知服务公共逻辑(签到/签退、报名成功 等共用)

- 活动级去重: activity_notifications(act_id, type) 每活动每类型只发一次
- 活动 payload 组装(给 wechat_notify)
- 按名单 role 分流发送: role==1 老师/组织(模板B,绑 admin) / 其余学生(模板A/C,绑 student)
  role 字段在 fetch_members 和 fetch_sign_records 两个接口都有,通用。
"""
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models import Activity, ActivityDetail, ActivityNotification
from app.repositories import binding_repo
from app.services import wechat_notify


def already_sent(db: Session, act_id: int, ntype: str) -> bool:
    return db.query(ActivityNotification).filter(
        ActivityNotification.act_id == act_id,
        ActivityNotification.notification_type == ntype,
    ).first() is not None


def mark_sent(db: Session, act_id: int, ntype: str, recipient: int, success: int, fail: int) -> None:
    db.add(ActivityNotification(
        act_id=act_id,
        notification_type=ntype,
        sent_at=datetime.now(),
        recipient_count=recipient,
        success_count=success,
        fail_count=fail,
    ))
    db.commit()


def activity_payload(db: Session, act: Activity) -> Dict[str, Any]:
    """组装给 wechat_notify 的活动 dict。"""
    detail = db.query(ActivityDetail).filter(ActivityDetail.act_id == act.act_id).first()
    return {
        "name": act.name,
        "act_id": act.act_id,
        "start_time": act.start_time,
        "enroll_end_time": act.enroll_end_time,
        "pitch_address": detail.pitch_address if detail else None,
    }


def send_to_members(
    db: Session,
    act: Activity,
    records: List[Dict],
    scene: str,
    admin_result: str,
    admin_note: str = "",
) -> Dict[str, int]:
    """给名单里的人发通知(学生 scene 模板 / 老师 admin 模板)。返回 {recipient, success, fail}。

    scene: enrollable / enrolled / sign_in / sign_out (学生模板,见 wechat_notify)
    admin_result: 老师模板 B 的 phrase1(≤5字)
    """
    payload = activity_payload(db, act)
    recipient = success = fail = 0

    for r in records:
        code = str(r.get("code") or "").strip()
        if not code:
            continue
        # role==1 组织/老师(短工号), role 2/3 学生(8位学号)
        is_teacher = r.get("role") == 1

        if is_teacher:
            for oid in binding_repo.openids_by_code(db, code, "admin"):
                recipient += 1
                res = wechat_notify.notify_admin(oid, payload, admin_result, note=admin_note)
                ok = res.get("errcode") == 0
                success += 1 if ok else 0
                fail += 0 if ok else 1
        else:
            for oid in binding_repo.openids_by_code(db, code, "student"):
                recipient += 1
                res = wechat_notify.notify(oid, scene, payload)
                ok = res.get("errcode") == 0
                success += 1 if ok else 0
                fail += 0 if ok else 1

    return {"recipient": recipient, "success": success, "fail": fail}
