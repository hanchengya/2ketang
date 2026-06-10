#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫日志数据模型
"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base
from enum import Enum


class CrawlerTaskType(str, Enum):
    """爬虫任务类型"""
    activities = "activities"  # 活动列表
    details = "details"  # 活动详情
    students = "students"  # 学生信息
    participants = "participants"  # 参与者信息
    full = "full"  # 综合爬取(列表+详情+参与者)
    # 生命周期通知(新架构,经 wechat_notify)
    notify_enrollable = "notify_enrollable"  # 可报名通知
    notify_enrolled = "notify_enrolled"      # 报名成功通知
    notify_sign = "notify_sign"              # 签到/签退通知
    # 自动化通知脚本类型(旧)
    script_new_activity = "script_new_activity"  # 新活动报名通知脚本
    script_sign_in = "script_sign_in"  # 签到通知脚本
    script_sign_out = "script_sign_out"  # 签退通知脚本


class CrawlerTaskStatus(str, Enum):
    """爬虫任务状态"""
    pending = "pending"  # 等待中
    running = "running"  # 运行中
    stopped = "stopped"  # 已停止
    completed = "completed"  # 已完成
    failed = "failed"  # 失败


class CrawlerLog(Base):
    """爬虫日志表"""
    __tablename__ = "crawler_logs"

    # 自增ID（主键）
    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增ID")
    
    # 任务ID（UUID，用于内部追踪）
    task_id = Column(String(36), nullable=False, index=True, comment="任务ID")

    # 任务类型（使用String直接存储，避免Enum兼容性问题）
    task_type = Column(
        String(20),
        nullable=False,
        comment="任务类型"
    )

    # 任务状态
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="任务状态"
    )

    # 进度信息
    current_count = Column(Integer, default=0, comment="当前进度")
    total_count = Column(Integer, default=0, comment="总数")

    # 日志内容（追加式，每次新增日志添加到末尾）
    log_content = Column(Text, default="", comment="日志内容")

    # 时间信息
    started_at = Column(TIMESTAMP, comment="开始时间")
    finished_at = Column(TIMESTAMP, comment="完成时间")
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )

    def __repr__(self):
        return f"<CrawlerLog(task_id={self.task_id}, type={self.task_type}, status={self.status})>"
