"""
公开只读 API (无需 admin 认证)

给微信小程序学生端使用。所有接口仅返回非敏感的活动信息,
不暴露管理员邮件日志、爬虫状态等内部数据。
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Activity, ActivityDetail

router = APIRouter()

# 学生端默认隐藏的状态 (审核流相关 / 异常态)
HIDDEN_STATUSES = {"审核中", "被驳回", "完结审核中", "完结被驳回"}


def _to_iso(dt):
    return dt.isoformat() if dt else None


@router.get("/activities")
def list_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    finish_status: str = Query("", description="报名中 / 进行中 / 已结束 / 待审核"),
    keyword: str = Query("", description="按活动名 / 主办方搜索"),
    db: Session = Depends(get_db),
) -> Any:
    """
    活动列表。状态以平台 tab 标签为准 (爬虫维护)。
    默认隐藏 审核中 / 被驳回 / 完结审核中 / 完结被驳回 这类对学生不可见的状态。
    """
    query = db.query(Activity)

    fs = finish_status.strip()
    if fs:
        query = query.filter(Activity.finish_status == fs)
    else:
        query = query.filter(~Activity.finish_status.in_(HIDDEN_STATUSES))

    kw = keyword.strip()
    if kw:
        like = f"%{kw}%"
        query = query.filter(or_(Activity.name.like(like), Activity.org_name.like(like)))

    total = query.count()
    rows = (
        query.order_by(Activity.start_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "items": [
            {
                "act_id": a.act_id,
                "act_name": a.name,
                "class_name": a.class_name,
                "org_name": a.org_name,
                "start_time": _to_iso(a.start_time),
                "end_time": _to_iso(a.end_time),
                "enroll_end_time": _to_iso(a.enroll_end_time),
                "hours": float(a.hours) if a.hours else None,
                "finish_status": a.finish_status or "",
            }
            for a in rows
        ],
    }


@router.get("/activities/stats")
def activity_stats(db: Session = Depends(get_db)) -> Any:
    """
    首页用的活动概况。
    total: 学生可见的活动总数 (排除审核流相关状态)
    enrolling: 报名中
    ongoing: 进行中
    """
    base = db.query(Activity).filter(~Activity.finish_status.in_(HIDDEN_STATUSES))
    return {
        "total": base.count(),
        "enrolling": base.filter(Activity.finish_status == "报名中").count(),
        "ongoing": base.filter(Activity.finish_status == "进行中").count(),
    }


@router.get("/activities/{act_id}")
def activity_detail(act_id: int, db: Session = Depends(get_db)) -> Any:
    """活动详情。"""
    detail = db.query(ActivityDetail).filter(ActivityDetail.act_id == act_id).first()
    if not detail:
        raise HTTPException(status_code=404, detail="活动不存在")

    activity = db.query(Activity).filter(Activity.act_id == act_id).first()
    finish_status = activity.finish_status if activity else None

    qq_list = []
    if detail.qq_groups:
        qq_list = [s.strip() for s in str(detail.qq_groups).split(",") if s.strip()]

    return {
        "act_id": detail.act_id,
        "act_name": detail.act_name,
        "introduce": detail.introduce or "",
        "org_name": detail.org_name,
        "class_name": detail.class_name,
        "type_name": detail.type_name,
        "start_time": _to_iso(detail.start_time),
        "end_time": _to_iso(detail.end_time),
        "enroll_end_time": _to_iso(detail.enroll_end_time),
        "pitch_address": detail.pitch_address,
        "college_name": detail.college_name,
        "grade_name": detail.grade_name,
        "people_limit": detail.people_limit,
        "hours": float(detail.hours) if detail.hours else None,
        "qq_groups": qq_list,
        "finish_status": finish_status or "",
        "job": detail.job,
    }
