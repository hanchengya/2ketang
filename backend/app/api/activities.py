#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动管理API
"""
from __future__ import annotations

from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, ConfigDict, model_serializer
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models import Activity, ActivityDetail, User
from app.models.notification import ActivityParticipant

router = APIRouter()


class ActivityInfo(BaseModel):
    """活动信息"""
    model_config = ConfigDict(from_attributes=True)

    act_id: int
    name: str
    class_name: Optional[str] = None
    org_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    enroll_end_time: Optional[datetime] = None
    hours: Optional[float] = None
    status: Optional[int] = None
    status_all: Optional[int] = None
    finish_status: Optional[str] = None


class ActivityDetailInfo(BaseModel):
    """活动详情信息"""
    act_id: int
    act_name: str
    introduce: Optional[str] = None
    org_name: Optional[str] = None
    class_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    enroll_end_time: Optional[datetime] = None
    pitch_address: Optional[str] = None
    college_name: Optional[str] = None
    grade_name: Optional[str] = None
    people_limit: Optional[int] = None
    hours: Optional[float] = None
    job: Optional[int] = None
    qq_groups: Optional[str] = None
    finish_status: Optional[str] = None

    class Config:
        from_attributes = True


class ActivityListResponse(BaseModel):
    """活动列表响应"""
    total: int
    items: List[ActivityInfo]


@router.get("")
@router.get("/")
def get_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(""),
    finish_status: str = Query(""),
    org_name: str = Query(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取活动列表

    Args:
        skip: 跳过数量
        limit: 返回数量
        status: 状态筛选
        finish_status: 完成状态筛选（待审核、报名中、进行中、已结束）
        org_name: 主办方筛选
        db: 数据库会话
        current_user: 当前用户

    Returns:
        活动列表
    """
    query = db.query(Activity)

    # 筛选条件
    if status and status.strip():
        try:
            status_int = int(status)
            query = query.filter(Activity.status == status_int)
        except ValueError:
            pass
    if finish_status and finish_status.strip():
        query = query.filter(Activity.finish_status == finish_status)
    if org_name and org_name.strip():
        query = query.filter(Activity.org_name.like(f"%{org_name}%"))

    # 总数
    total = query.count()

    # 分页，按开始时间倒序
    activities = query.order_by(Activity.start_time.desc()).offset(skip).limit(limit).all()

    # 手动转换数据
    items = []
    for a in activities:
        items.append({
            'act_id': a.act_id,
            'act_name': a.name,  # 将 name 转换为 act_name
            'class_name': a.class_name,
            'org_name': a.org_name,
            'start_time': a.start_time,
            'end_time': a.end_time,
            'enroll_end_time': a.enroll_end_time,
            'hours': float(a.hours) if a.hours else None,
            'status': a.status,
            'status_all': a.status_all,
            'finish_status': a.finish_status or ''
        })

    return {'total': total, 'items': items}


@router.get("/{act_id}", response_model=ActivityDetailInfo)
def get_activity_detail(
    act_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取活动详情

    Args:
        act_id: 活动ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        活动详情
    """
    detail = db.query(ActivityDetail).filter(ActivityDetail.act_id == act_id).first()
    if not detail:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Activity not found")

    # 从主活动表获取finish_status
    activity = db.query(Activity).filter(Activity.act_id == act_id).first()
    finish_status = activity.finish_status if activity else None
    
    # 构建返回数据
    result = {
        'act_id': detail.act_id,
        'act_name': detail.act_name,
        'introduce': detail.introduce,
        'org_name': detail.org_name,
        'class_name': detail.class_name,
        'start_time': detail.start_time,
        'end_time': detail.end_time,
        'enroll_end_time': detail.enroll_end_time,
        'pitch_address': detail.pitch_address,
        'college_name': detail.college_name,
        'grade_name': detail.grade_name,
        'people_limit': detail.people_limit,
        'hours': detail.hours,
        'job': detail.job,
        'qq_groups': detail.qq_groups,
        'finish_status': finish_status
    }
    
    return result


@router.get("/stats/summary")
def get_activity_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取活动统计信息

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        统计信息
    """
    from sqlalchemy import func

    # 总活动数
    total = db.query(Activity).count()

    # 按 finish_status 分组统计（实际爬取的状态）
    status_counts = db.query(
        Activity.finish_status,
        func.count(Activity.act_id).label('count')
    ).group_by(Activity.finish_status).all()

    # 构建按状态分类的统计
    by_status = {}
    for status, count in status_counts:
        status_name = status if status else '未知'
        by_status[status_name] = count

    return {
        "total": total,
        "by_status": by_status
    }


class ParticipantInfo(BaseModel):
    """参与者信息"""
    id: int
    act_id: int
    student_code: str
    student_name: Optional[str] = None
    sign_in_time: Optional[datetime] = None
    sign_out_time: Optional[datetime] = None
    credits: Optional[float] = None

    class Config:
        from_attributes = True


@router.get("/{act_id}/participants")
def get_activity_participants(
    act_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取活动参与者列表

    Args:
        act_id: 活动ID
        skip: 跳过数量
        limit: 返回数量
        db: 数据库会话
        current_user: 当前用户

    Returns:
        参与者列表
    """
    query = db.query(ActivityParticipant).filter(ActivityParticipant.act_id == act_id)
    
    total = query.count()
    participants = query.offset(skip).limit(limit).all()
    
    items = []
    for p in participants:
        items.append({
            'id': p.id,
            'act_id': p.act_id,
            'student_code': p.student_code,
            'student_name': p.student_name,
            'sign_in_time': p.sign_in_time.strftime('%Y-%m-%d %H:%M:%S') if p.sign_in_time else None,
            'sign_out_time': p.sign_out_time.strftime('%Y-%m-%d %H:%M:%S') if p.sign_out_time else None,
            'credits': float(p.credits) if p.credits else None
        })
    
    return {
        "total": total,
        "items": items
    }
