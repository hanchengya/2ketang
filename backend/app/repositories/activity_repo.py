#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动 / 活动详情 数据访问层
(从 crawler_service._save_activities_to_db / _save_activity_details_to_db 抽出)
"""
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import Activity, ActivityDetail
from app.utils.parse import to_datetime

log = get_logger(__name__)


def save_activities(db: Session, activities_dict: Dict[str, List[Dict[str, Any]]]) -> int:
    """按 tab 分组的活动 upsert。tab 名即活动状态(平台 finishStatus 优先)。返回保存条数。"""
    total = 0
    for tab_name, activities in activities_dict.items():
        for activity in activities:
            try:
                # 平台 finishStatus 优先,否则用 tab 名
                status = activity.get("finishStatus") or tab_name

                existing = db.query(Activity).filter(
                    Activity.act_id == activity.get("actId")
                ).first()

                if existing:
                    existing.start_time = to_datetime(activity.get("startTime"))
                    existing.end_time = to_datetime(activity.get("endTime"))
                    existing.enroll_end_time = to_datetime(activity.get("enrollEndTime"))
                    existing.finish_status = status
                    existing.finish_status2 = activity.get("finishStatus2", "")
                else:
                    db.add(Activity(
                        act_id=activity.get("actId"),
                        name=activity.get("name"),
                        class_id=activity.get("classId"),
                        class_name=activity.get("className"),
                        org_id=activity.get("orgId"),
                        org_name=activity.get("orgName"),
                        admin_id=activity.get("adminId"),
                        admin_code=activity.get("adminCode"),
                        admin_name=activity.get("adminName"),
                        creator_id=activity.get("creatorId"),
                        hours=activity.get("hours"),
                        start_time=to_datetime(activity.get("startTime")),
                        end_time=to_datetime(activity.get("endTime")),
                        enroll_end_time=to_datetime(activity.get("enrollEndTime")),
                        status=activity.get("status"),
                        apply_status=activity.get("applyStatus"),
                        status_all=activity.get("statusAll"),
                        oto=activity.get("oto"),
                        edit_activity=activity.get("editActivity"),
                        chenge_status=activity.get("chengeStatus"),
                        finish_status=status,
                        finish_status2=activity.get("finishStatus2"),
                    ))
                total += 1
            except Exception:
                log.exception("保存活动失败 act_id=%s", activity.get("actId"))

    db.commit()
    return total


def save_details(db: Session, details: List[Dict[str, Any]]) -> int:
    """活动详情 upsert。返回保存条数。"""
    total = 0
    for detail in details:
        try:
            existing = db.query(ActivityDetail).filter(
                ActivityDetail.act_id == detail.get("actId")
            ).first()

            if existing:
                existing.introduce = detail.get("introduce")
                existing.college_name = detail.get("collegeName")
                existing.grade_name = detail.get("gradeName")
                existing.qq_groups = detail.get("qq_groups")
            else:
                db.add(ActivityDetail(
                    act_id=detail.get("actId"),
                    act_name=detail.get("actName"),
                    introduce=detail.get("introduce"),
                    org_id=detail.get("orgId"),
                    org_name=detail.get("orgName"),
                    class_id=detail.get("classId"),
                    class_name=detail.get("calssName"),  # 注意原数据拼写
                    start_time=to_datetime(detail.get("starTime")),
                    end_time=to_datetime(detail.get("endTime")),
                    enroll_end_time=to_datetime(detail.get("enrollEndTime")),
                    hours=detail.get("hours"),
                    people_limit=detail.get("peopleLimit"),
                    pitch_address=detail.get("pitchAddress"),
                    college_name=detail.get("collegeName"),
                    grade_name=detail.get("gradeName"),
                    job=detail.get("job"),
                    qq_groups=detail.get("qq_groups"),
                ))
            total += 1
        except Exception:
            log.exception("保存活动详情失败 act_id=%s", detail.get("actId"))

    db.commit()
    return total
