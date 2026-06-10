#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报名成功 通知服务 (需求 #4)

对"待开始"的活动:
  1. fetch_members(act_id) 拉报名列表
  2. 给报名者发"报名成功"(学生模板 A thing5="报名成功" / 老师模板 B)
  3. 活动级去重: activity_notifications(act_id, "enrolled") 每活动只发一次
     (活动进入"待开始"时报名已截止,名单固定,一次性全发即可)

只有"绑定学号 + 授权过模板"的人能真正收到(微信订阅消息机制)。
"""
from typing import Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.crawlers.activity_api import fetch_members
from app.models import Activity
from app.services import notify_common

log = get_logger(__name__)


def run_enrolled_notify(
    db: Session,
    driver,
    act_ids: Optional[List[int]] = None,
    stop_check: Optional[Callable[[], bool]] = None,
    log_fn: Callable[[str], None] = lambda m: None,
) -> Dict[str, int]:
    """给待开始活动的报名者发"报名成功"通知。

    Args:
        driver: 已登录 driver(fetch_members 需要登录态)
        act_ids: 指定活动;None 则取所有"待开始"活动
    Returns:
        汇总统计
    """
    if act_ids:
        acts = db.query(Activity).filter(Activity.act_id.in_(act_ids)).all()
    else:
        acts = db.query(Activity).filter(Activity.finish_status == "待开始").all()

    summary = {"checked": 0, "sent": 0, "msg_success": 0, "msg_fail": 0}
    log_fn(f"待检查(待开始)活动 {len(acts)} 个")

    for act in acts:
        if stop_check and stop_check():
            log_fn("收到停止信号")
            break

        # 已发过就跳过(连名单都不用拉,省时间)
        if notify_common.already_sent(db, act.act_id, "enrolled"):
            continue

        try:
            members = fetch_members(driver, act.act_id)
        except Exception:
            log.exception("拉报名列表失败 act_id=%s", act.act_id)
            continue

        summary["checked"] += 1
        if not members:
            continue

        res = notify_common.send_to_members(
            db, act, members, "enrolled",
            admin_result="报名成功", admin_note="活动报名情况",
        )
        notify_common.mark_sent(db, act.act_id, "enrolled",
                                res["recipient"], res["success"], res["fail"])
        summary["sent"] += 1
        summary["msg_success"] += res["success"]
        summary["msg_fail"] += res["fail"]
        log_fn(f"[{act.act_id}] 报名成功通知: 报名 {len(members)} 人 → 触达 {res['recipient']} (成功 {res['success']})")

    log_fn(f"完成: 检查 {summary['checked']} 活动, 发送 {summary['sent']}, "
           f"消息成功 {summary['msg_success']} 失败 {summary['msg_fail']}")
    return summary
