#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知相关模型
"""
from sqlalchemy import Column, String, Integer, DECIMAL, DATETIME, TIMESTAMP, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class NotificationType(str, enum.Enum):
    """通知类型枚举"""
    NEW_ACTIVITY = "new_activity"   # 可报名通知
    ENROLLED = "enrolled"           # 报名成功通知
    SIGN_IN = "sign_in"             # 签到通知
    SIGN_OUT = "sign_out"           # 签退通知


class EmailStatus(str, enum.Enum):
    """邮件状态枚举"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ActivityNotification(Base):
    """活动通知记录表"""
    __tablename__ = "activity_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    act_id = Column(Integer, nullable=False, comment="活动ID", index=True)
    notification_type = Column(
        String(50),  # 改用String类型以避免枚举值不匹配
        nullable=False,
        comment="通知类型"
    )
    sent_at = Column(DATETIME, nullable=False, comment="发送时间", index=True)
    recipient_count = Column(Integer, default=0, comment="接收人数")
    success_count = Column(Integer, default=0, comment="成功发送数")
    fail_count = Column(Integer, default=0, comment="失败发送数")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<ActivityNotification(act_id={self.act_id}, type={self.notification_type})>"


class ActivityParticipant(Base):
    """活动参与者表"""
    __tablename__ = "activity_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    act_id = Column(Integer, nullable=False, comment="活动ID", index=True)
    student_code = Column(String(50), nullable=False, comment="学号", index=True)
    student_name = Column(String(100), comment="学生姓名")
    sign_in_time = Column(DATETIME, comment="签到时间")
    sign_out_time = Column(DATETIME, comment="签退时间")
    credits = Column(DECIMAL(5, 2), comment="获得学分")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ActivityParticipant(act_id={self.act_id}, student_code={self.student_code})>"


class EmailLog(Base):
    """邮件发送日志表"""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    act_id = Column(Integer, nullable=False, comment="活动ID", index=True)
    recipient_email = Column(String(255), nullable=False, comment="收件人邮箱", index=True)
    student_code = Column(String(50), comment="学号", index=True)
    email_type = Column(
        String(50),  # 改用String类型以避免枚举值不匹配
        nullable=False,
        comment="邮件类型"
    )
    subject = Column(String(500), comment="邮件主题")
    status = Column(
        String(20),  # 改用String类型以避免枚举值不匹配
        default="pending",
        comment="发送状态",
        index=True
    )
    error_message = Column(String(1000), comment="错误信息")
    sent_at = Column(DATETIME, comment="发送时间", index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<EmailLog(id={self.id}, recipient={self.recipient_email}, status={self.status})>"
