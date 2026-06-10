"""
公开只读 API (无需 admin 认证)

给微信小程序学生端使用。所有接口仅返回非敏感的活动信息,
不暴露管理员邮件日志、爬虫状态等内部数据。
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Activity, ActivityDetail
from app.repositories import binding_repo

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
    """活动详情。详情表无数据时降级用主表字段拼一个,不直接 404。"""
    detail = db.query(ActivityDetail).filter(ActivityDetail.act_id == act_id).first()
    activity = db.query(Activity).filter(Activity.act_id == act_id).first()

    if not activity and not detail:
        raise HTTPException(status_code=404, detail="活动不存在")

    # 详情未爬取: 主表字段拼一个简化版返回
    if not detail:
        return {
            "act_id": activity.act_id,
            "act_name": activity.name,
            "introduce": "",
            "org_name": activity.org_name,
            "class_name": activity.class_name,
            "type_name": None,
            "start_time": _to_iso(activity.start_time),
            "end_time": _to_iso(activity.end_time),
            "enroll_end_time": _to_iso(activity.enroll_end_time),
            "pitch_address": None,
            "college_name": None,
            "grade_name": None,
            "people_limit": None,
            "hours": float(activity.hours) if activity.hours else None,
            "qq_groups": [],
            "finish_status": activity.finish_status or "",
            "job": None,
            "detail_pending": True,
        }

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
        "detail_pending": False,
    }


# ============ 微信绑定 / 订阅额度 ============

class BindRequest(BaseModel):
    openid: str
    role: str = "student"   # student(本人学号) / admin(管理员账号)
    code: str               # 学号 / 工号
    name: str


@router.post("/bind")
def bind(req: BindRequest, db: Session = Depends(get_db)) -> Any:
    """绑定学号/管理员账号。

    - student: 严格校验 学号+姓名 与 students 表匹配
    - admin:   老师验证系统尚未就绪(需求注明"后面额外设计"),本期暂不强校验,仅记录
    """
    if req.role not in ("student", "admin"):
        raise HTTPException(status_code=400, detail="role 只能是 student 或 admin")
    if not req.openid:
        raise HTTPException(status_code=400, detail="缺少 openid")

    code = (req.code or "").strip()
    name = (req.name or "").strip()
    if not code or not name:
        raise HTTPException(status_code=400, detail="学号和姓名不能为空")

    if req.role == "student":
        if not binding_repo.verify_student(db, code, name):
            raise HTTPException(status_code=400, detail="学号与姓名不匹配,请核对后重试")
    # TODO(老师验证系统): admin 角色目前不强校验,等老师/工号数据源就绪后补上

    b = binding_repo.upsert_binding(db, req.openid, req.role, code, name)
    return {"ok": True, "role": b.role, "code": b.code, "name": b.name}


class UnbindRequest(BaseModel):
    openid: str
    role: str = "student"


@router.post("/unbind")
def unbind(req: UnbindRequest, db: Session = Depends(get_db)) -> Any:
    """解绑指定角色。"""
    ok = binding_repo.remove_binding(db, req.openid, req.role)
    return {"ok": ok}


@router.get("/binding")
def get_binding(openid: str = Query(...), db: Session = Depends(get_db)) -> Any:
    """查某 openid 的绑定状态(student / admin 各最多一条)。"""
    rows = binding_repo.get_bindings(db, openid)
    return {
        "bindings": [
            {"role": r.role, "code": r.code, "name": r.name} for r in rows
        ]
    }


class SubscribeRequest(BaseModel):
    openid: str
    template_id: str
    count: int = 1


@router.post("/subscribe")
def subscribe(req: SubscribeRequest, db: Session = Depends(get_db)) -> Any:
    """小程序 requestSubscribeMessage 授权成功后回调,额度 +count。"""
    if not req.openid or not req.template_id:
        raise HTTPException(status_code=400, detail="缺少 openid 或 template_id")
    remaining = binding_repo.add_quota(db, req.openid, req.template_id, max(1, req.count))
    return {"ok": True, "remaining": remaining}
