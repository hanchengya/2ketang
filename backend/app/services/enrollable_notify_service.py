#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可报名 通知服务 (需求 #3)

对"报名中"的活动,给"有参与权限"的已绑定学生发"可以报名了"通知(模板 C)。

权限 = 活动详情的院系/年级限制,匹配学生的 college_name/grade_name("不限"→全部)。
只发给已绑定 student 的学生(微信订阅消息只能发给授权用户),所以遍历绑定学生(少)
逐个判断是否符合活动条件,比拉全表高效。

注意: 报名中活动的详情(college/grade)综合爬取默认不爬(只爬待开始/进行中),
本服务对缺详情的报名中活动会用 selenium 补爬一次并入库。

活动级去重: activity_notifications(act_id, "new_activity") 每活动只发一次。
"""
from typing import Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.crawlers.detail_crawler import crawl_activity_detail
from app.models import Activity, ActivityDetail, WxBinding, Student
from app.repositories import activity_repo
from app.services import notify_common, student_matcher, wechat_notify

log = get_logger(__name__)


def _ensure_detail(db: Session, driver, act_id: int) -> Optional[ActivityDetail]:
    """读详情;缺则 selenium 补爬一次并入库。返回 ActivityDetail 或 None。"""
    detail = db.query(ActivityDetail).filter(ActivityDetail.act_id == act_id).first()
    if detail:
        return detail
    try:
        d = crawl_activity_detail(driver, act_id)
        if d:
            activity_repo.save_details(db, [d])
            return db.query(ActivityDetail).filter(ActivityDetail.act_id == act_id).first()
    except Exception:
        log.exception("补爬活动详情失败 act_id=%s", act_id)
    return None


def run_enrollable_notify(
    db: Session,
    driver,
    act_ids: Optional[List[int]] = None,
    stop_check: Optional[Callable[[], bool]] = None,
    log_fn: Callable[[str], None] = lambda m: None,
) -> Dict[str, int]:
    """给报名中活动的有权限已绑定学生发"可报名"通知。"""
    # 预取已绑定的学生 {学号: openid} —— 没人绑定就不用爬,直接返回
    bindings = db.query(WxBinding).filter(WxBinding.role == "student").all()
    if not bindings:
        log_fn("没有已绑定的学生,跳过(可报名通知只能发给已绑定+授权的学生)")
        return {"checked": 0, "sent": 0, "msg_success": 0, "msg_fail": 0}

    code_to_openid: Dict[str, str] = {b.code: b.openid for b in bindings}
    # 取这些绑定学号对应的 student 记录(判断院系/年级用)
    students = db.query(Student).filter(Student.code.in_(list(code_to_openid.keys()))).all()
    code_to_student: Dict[str, Student] = {s.code: s for s in students}

    if act_ids:
        acts = db.query(Activity).filter(Activity.act_id.in_(act_ids)).all()
    else:
        acts = db.query(Activity).filter(Activity.finish_status == "报名中").all()

    summary = {"checked": 0, "sent": 0, "msg_success": 0, "msg_fail": 0}
    log_fn(f"待检查(报名中)活动 {len(acts)} 个,已绑定学生 {len(code_to_openid)} 人")

    for act in acts:
        if stop_check and stop_check():
            log_fn("收到停止信号")
            break
        if notify_common.already_sent(db, act.act_id, "new_activity"):
            continue

        detail = _ensure_detail(db, driver, act.act_id)
        if not detail:
            log_fn(f"[{act.act_id}] 无详情(补爬失败),跳过")
            continue
        summary["checked"] += 1

        payload = notify_common.activity_payload(db, act)
        recipient = success = fail = 0
        for code, openid in code_to_openid.items():
            stu = code_to_student.get(code)
            if not stu:
                continue
            if student_matcher.student_matches(stu, detail.college_name, detail.grade_name):
                recipient += 1
                res = wechat_notify.notify(openid, "enrollable", payload)
                ok = res.get("errcode") == 0
                success += 1 if ok else 0
                fail += 0 if ok else 1

        if recipient > 0:
            notify_common.mark_sent(db, act.act_id, "new_activity", recipient, success, fail)
            summary["sent"] += 1
            summary["msg_success"] += success
            summary["msg_fail"] += fail
            log_fn(f"[{act.act_id}] 可报名通知: 符合条件已绑定 {recipient} 人 (成功 {success})")

    log_fn(f"完成: 检查 {summary['checked']} 活动, 发送 {summary['sent']}, "
           f"消息成功 {summary['msg_success']} 失败 {summary['msg_fail']}")
    return summary
