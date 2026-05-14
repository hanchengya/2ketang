#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫任务管理器
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from app.models.crawler_log import CrawlerLog, CrawlerTaskType, CrawlerTaskStatus


class CrawlerTaskManager:
    """
    爬虫任务管理器（单例模式）
    管理所有爬虫任务的状态和日志
    """
    _instance = None
    _tasks: Dict[str, dict] = {}  # 内存中的任务状态缓存

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._tasks = {}
        return cls._instance

    def create_task(
        self,
        task_type: CrawlerTaskType,
        db: Session,
        total_count: int = 0
    ) -> str:
        """
        创建新任务

        Args:
            task_type: 任务类型
            db: 数据库会话
            total_count: 总数

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())

        # 创建数据库记录
        crawler_log = CrawlerLog(
            task_id=task_id,
            task_type=task_type,
            status=CrawlerTaskStatus.pending,
            current_count=0,
            total_count=total_count,
            log_content="",
            started_at=None,
            finished_at=None
        )
        db.add(crawler_log)
        db.commit()

        # 内存缓存
        self._tasks[task_id] = {
            "task_type": task_type,
            "status": CrawlerTaskStatus.pending,
            "should_stop": False,  # 停止信号
            "current_count": 0,
            "total_count": total_count
        }

        self.append_log(task_id, db, f"任务创建: {task_type.value}")
        return task_id

    def update_status(
        self,
        task_id: str,
        db: Session,
        status: CrawlerTaskStatus,
        log_message: Optional[str] = None
    ):
        """
        更新任务状态

        Args:
            task_id: 任务ID
            db: 数据库会话
            status: 新状态
            log_message: 日志消息
        """
        if task_id not in self._tasks:
            return

        # 更新内存状态
        self._tasks[task_id]["status"] = status

        # 更新数据库
        crawler_log = db.query(CrawlerLog).filter(CrawlerLog.task_id == task_id).first()
        if crawler_log:
            crawler_log.status = status

            # 设置时间戳
            if status == CrawlerTaskStatus.running and not crawler_log.started_at:
                crawler_log.started_at = datetime.now()
            elif status in [CrawlerTaskStatus.completed, CrawlerTaskStatus.failed, CrawlerTaskStatus.stopped]:
                crawler_log.finished_at = datetime.now()

            db.commit()

        # 添加日志
        if log_message:
            self.append_log(task_id, db, log_message)

    def update_progress(
        self,
        task_id: str,
        db: Session,
        current_count: int,
        total_count: Optional[int] = None
    ):
        """
        更新任务进度

        Args:
            task_id: 任务ID
            db: 数据库会话
            current_count: 当前进度
            total_count: 总数（可选）
        """
        if task_id not in self._tasks:
            return

        # 更新内存
        self._tasks[task_id]["current_count"] = current_count
        if total_count is not None:
            self._tasks[task_id]["total_count"] = total_count

        # 更新数据库
        crawler_log = db.query(CrawlerLog).filter(CrawlerLog.task_id == task_id).first()
        if crawler_log:
            crawler_log.current_count = current_count
            if total_count is not None:
                crawler_log.total_count = total_count
            db.commit()

    def append_log(
        self,
        task_id: str,
        db: Session,
        message: str
    ):
        """
        追加日志内容

        Args:
            task_id: 任务ID
            db: 数据库会话
            message: 日志消息
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"

        # 更新数据库
        crawler_log = db.query(CrawlerLog).filter(CrawlerLog.task_id == task_id).first()
        if crawler_log:
            if crawler_log.log_content:
                crawler_log.log_content += log_line
            else:
                crawler_log.log_content = log_line
            db.commit()

        # 打印到控制台
        print(f"[Task {task_id[:8]}] {message}")

    def request_stop(self, task_id: str, db: Session):
        """
        请求停止任务

        Args:
            task_id: 任务ID
            db: 数据库会话
        """
        if task_id in self._tasks:
            self._tasks[task_id]["should_stop"] = True
            self.append_log(task_id, db, "收到停止请求")

    def should_stop(self, task_id: str) -> bool:
        """
        检查是否应该停止

        Args:
            task_id: 任务ID

        Returns:
            是否应该停止
        """
        if task_id not in self._tasks:
            return False
        return self._tasks[task_id].get("should_stop", False)

    def get_task_info(self, task_id: str, db: Session) -> Optional[Dict]:
        """
        获取任务信息

        Args:
            task_id: 任务ID
            db: 数据库会话

        Returns:
            任务信息字典
        """
        crawler_log = db.query(CrawlerLog).filter(CrawlerLog.task_id == task_id).first()
        if not crawler_log:
            return None

        return {
            "task_id": crawler_log.task_id,
            "task_type": str(crawler_log.task_type),
            "status": str(crawler_log.status),
            "current_count": crawler_log.current_count,
            "total_count": crawler_log.total_count,
            "log_content": crawler_log.log_content or "",
            "started_at": crawler_log.started_at.isoformat() if crawler_log.started_at else None,
            "finished_at": crawler_log.finished_at.isoformat() if crawler_log.finished_at else None,
            "created_at": crawler_log.created_at.isoformat() if crawler_log.created_at else None
        }

    def get_all_tasks(self, db: Session) -> List[Dict]:
        """
        获取所有任务列表

        Args:
            db: 数据库会话

        Returns:
            任务列表
        """
        # 强制刷新会话，确保获取最新数据
        db.expire_all()
        crawler_logs = db.query(CrawlerLog).order_by(CrawlerLog.id.desc()).all()
        return [
            {
                "id": log.id,
                "task_id": log.task_id,
                "task_type": str(log.task_type),
                "status": str(log.status),
                "current_count": log.current_count,
                "total_count": log.total_count,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "finished_at": log.finished_at.isoformat() if log.finished_at else None,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in crawler_logs
        ]

    def get_running_tasks(self, db: Session) -> List[Dict]:
        """
        获取正在运行的任务

        Args:
            db: 数据库会话

        Returns:
            运行中的任务列表
        """
        crawler_logs = db.query(CrawlerLog).filter(
            CrawlerLog.status == CrawlerTaskStatus.running
        ).all()
        return [
            {
                "task_id": log.task_id,
                "task_type": log.task_type.value,
                "status": log.status.value,
                "current_count": log.current_count,
                "total_count": log.total_count,
                "started_at": log.started_at.isoformat() if log.started_at else None
            }
            for log in crawler_logs
        ]

    def cleanup_task(self, task_id: str):
        """
        清理任务缓存

        Args:
            task_id: 任务ID
        """
        if task_id in self._tasks:
            del self._tasks[task_id]


# 全局单例实例
task_manager = CrawlerTaskManager()
