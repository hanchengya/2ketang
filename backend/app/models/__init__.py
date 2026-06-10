#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型
"""
from app.models.student import Student
from app.models.activity import Activity, ActivityDetail
from app.models.notification import (
    ActivityNotification,
    ActivityParticipant,
    EmailLog,
    NotificationType,
    EmailStatus
)
from app.models.user import User, UserRole
from app.models.crawler_log import CrawlerLog, CrawlerTaskType, CrawlerTaskStatus
from app.models.binding import WxBinding, SubscribeQuota

__all__ = [
    "Student",
    "Activity",
    "ActivityDetail",
    "ActivityNotification",
    "ActivityParticipant",
    "EmailLog",
    "User",
    "NotificationType",
    "EmailStatus",
    "UserRole",
    "CrawlerLog",
    "CrawlerTaskType",
    "CrawlerTaskStatus",
    "WxBinding",
    "SubscribeQuota"
]
