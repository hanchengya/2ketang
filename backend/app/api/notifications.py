#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知管理API
"""
from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models import ActivityNotification, EmailLog, User

router = APIRouter()


class NotificationInfo(BaseModel):
    """通知信息"""
    id: int
    act_id: int
    act_name: Optional[str] = None
    notification_type: str
    sent_at: datetime
    recipient_count: int
    success_count: int
    fail_count: int

    class Config:
        from_attributes = True


class EmailLogInfo(BaseModel):
    """邮件日志信息"""
    id: int
    act_id: int
    recipient_email: str
    student_code: Optional[str]
    email_type: str
    subject: Optional[str]
    status: str
    error_message: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """通知列表响应"""
    total: int
    items: List[NotificationInfo]


class EmailLogListResponse(BaseModel):
    """邮件日志列表响应"""
    total: int
    items: List[EmailLogInfo]


@router.get("", response_model=NotificationListResponse)
@router.get("/", response_model=NotificationListResponse)
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    notification_type: Optional[str] = None,
    act_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取通知记录列表

    Args:
        skip: 跳过数量
        limit: 返回数量
        notification_type: 通知类型筛选
        act_name: 活动名称筛选
        db: 数据库会话
        current_user: 当前用户

    Returns:
        通知列表
    """
    from app.models import Activity

    # Join Activity表获取活动名称
    query = db.query(ActivityNotification, Activity.name).outerjoin(
        Activity, ActivityNotification.act_id == Activity.act_id
    )

    # 筛选条件
    if notification_type:
        query = query.filter(ActivityNotification.notification_type == notification_type)
    if act_name:
        query = query.filter(Activity.name.like(f"%{act_name}%"))

    # 总数
    total = query.count()

    # 分页，按发送时间倒序
    results = query.order_by(ActivityNotification.sent_at.desc()).offset(skip).limit(limit).all()

    # 构建响应数据
    items = []
    for notification, activity_name in results:
        item_dict = {
            'id': notification.id,
            'act_id': notification.act_id,
            'act_name': activity_name or '未知活动',
            'notification_type': notification.notification_type,
            'sent_at': notification.sent_at,
            'recipient_count': notification.recipient_count,
            'success_count': notification.success_count,
            'fail_count': notification.fail_count
        }
        items.append(NotificationInfo(**item_dict))

    return NotificationListResponse(total=total, items=items)


@router.get("/email-logs", response_model=EmailLogListResponse)
def get_email_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    student_code: Optional[str] = None,
    recipient_email: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取邮件发送日志

    Args:
        skip: 跳过数量
        limit: 返回数量
        status: 状态筛选
        student_code: 学号筛选
        recipient_email: 收件人邮箱筛选
        db: 数据库会话
        current_user: 当前用户

    Returns:
        邮件日志列表
    """
    query = db.query(EmailLog)

    # 筛选条件
    if status:
        query = query.filter(EmailLog.status == status)
    if student_code:
        query = query.filter(EmailLog.student_code == student_code)
    if recipient_email:
        query = query.filter(EmailLog.recipient_email.like(f"%{recipient_email}%"))

    # 总数
    total = query.count()

    # 分页，按创建时间倒序
    logs = query.order_by(EmailLog.created_at.desc()).offset(skip).limit(limit).all()

    return EmailLogListResponse(
        total=total,
        items=[EmailLogInfo.model_validate(log) for log in logs]
    )


class TestEmailRequest(BaseModel):
    """测试邮件请求"""
    student_code: str


@router.post("/test-email")
def send_test_email(
    request: TestEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    发送测试邮件给指定学生

    Args:
        request: 测试邮件请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        发送结果
    """
    from app.models import Student, NotificationType
    from app.services.email_service import EmailService
    from app.utils.email_template import render_new_activity_email

    # 查询学生
    student = db.query(Student).filter(Student.code == request.student_code).first()
    if not student:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"未找到学号为 {request.student_code} 的学生")

    if not student.email:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"学生 {student.name} 没有设置邮箱")

    # 构造测试活动数据
    test_activity = {
        "act_id": 9999,
        "act_name": "【测试】Python编程技能培训",
        "class_name": "创新创业",
        "org_name": "数智维新工作室",
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "pitch_address": "信息楼A201",
        "job": 1,
        "introduce": "本次活动将介绍Python编程基础知识，包括数据类型、控制流程、函数定义等内容。欢迎感兴趣的同学报名参加！",
        "qq_groups": "123456789",
        "people_limit": 50,
        "enroll_end_time": datetime.now(),
        "college_name": "不限",
        "grade_name": "2023级"
    }

    # 渲染邮件内容
    html_content = render_new_activity_email(test_activity)
    subject = f"【二课通知】{test_activity['act_name']}可以报名了！"

    # 发送邮件 - 实际发送
    email_service = EmailService(db, test_mode=False)

    result = email_service.send_email(
        to_email=student.email,
        subject=subject,
        html_content=html_content,
        act_id=test_activity["act_id"],
        student_code=request.student_code,
        email_type=NotificationType.NEW_ACTIVITY
    )

    return {
        "success": result,
        "student_name": student.name,
        "student_email": student.email,
        "message": "邮件发送成功" if result else "邮件发送失败"
    }


@router.get("/stats/summary")
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取通知统计信息

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        统计信息
    """
    from app.models import Activity

    # 通知总数
    total = db.query(ActivityNotification).count()

    # 统计各状态的邮件数量
    sent_count = db.query(EmailLog).filter(EmailLog.status == "sent").count()
    failed_count = db.query(EmailLog).filter(EmailLog.status == "failed").count()
    pending_count = db.query(EmailLog).filter(EmailLog.status == "pending").count()

    # 获取最近5条通知记录（包含活动名称）
    recent_results = db.query(ActivityNotification, Activity.name).outerjoin(
        Activity, ActivityNotification.act_id == Activity.act_id
    ).order_by(ActivityNotification.sent_at.desc()).limit(5).all()

    recent_notifications = []
    for notification, activity_name in recent_results:
        recent_notifications.append({
            'id': notification.id,
            'act_id': notification.act_id,
            'act_name': activity_name or '未知活动',
            'notification_type': notification.notification_type,
            'sent_at': notification.sent_at.strftime('%Y-%m-%d %H:%M:%S') if notification.sent_at else None,
            'recipient_count': notification.recipient_count,
            'success_count': notification.success_count,
            'fail_count': notification.fail_count
        })

    return {
        "total": total,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "pending_count": pending_count,
        "recent_notifications": recent_notifications
    }
