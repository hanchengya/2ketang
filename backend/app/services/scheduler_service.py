#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时爬虫调度器服务
"""
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from enum import Enum


class SchedulerStatus(str, Enum):
    """调度器状态"""
    stopped = "stopped"
    running = "running"
    waiting = "waiting"


class CrawlerScheduler:
    """爬虫定时调度器"""
    
    def __init__(self):
        self._schedules: Dict[str, Dict[str, Any]] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._stop_events: Dict[str, threading.Event] = {}
    
    def start_schedule(
        self,
        schedule_id: str,
        crawler_type: str,
        interval_minutes: int,
        crawler_func: Callable,
        on_complete: Optional[Callable] = None
    ) -> bool:
        """
        启动定时任务
        
        Args:
            schedule_id: 调度ID
            crawler_type: 爬虫类型
            interval_minutes: 间隔时间（分钟）
            crawler_func: 爬虫执行函数
            on_complete: 完成回调函数
            
        Returns:
            是否启动成功
        """
        if schedule_id in self._schedules and self._schedules[schedule_id]["status"] == SchedulerStatus.running:
            return False
        
        stop_event = threading.Event()
        self._stop_events[schedule_id] = stop_event
        
        self._schedules[schedule_id] = {
            "crawler_type": crawler_type,
            "interval_minutes": interval_minutes,
            "status": SchedulerStatus.running,
            "next_run": datetime.now(),
            "last_run": None,
            "run_count": 0,
            "created_at": datetime.now()
        }
        
        def schedule_loop():
            while not stop_event.is_set():
                schedule = self._schedules.get(schedule_id)
                if not schedule:
                    break
                
                # 更新状态为运行中
                schedule["status"] = SchedulerStatus.running
                schedule["last_run"] = datetime.now()
                
                try:
                    # 执行爬虫
                    crawler_func()
                    schedule["run_count"] += 1
                    
                    if on_complete:
                        on_complete(schedule_id, True, None)
                except Exception as e:
                    if on_complete:
                        on_complete(schedule_id, False, str(e))
                
                if stop_event.is_set():
                    break
                
                # 更新下次运行时间
                schedule["status"] = SchedulerStatus.waiting
                schedule["next_run"] = datetime.fromtimestamp(
                    time.time() + interval_minutes * 60
                )
                
                # 等待间隔时间（每秒检查一次停止信号）
                for _ in range(interval_minutes * 60):
                    if stop_event.is_set():
                        break
                    time.sleep(1)
            
            # 清理
            if schedule_id in self._schedules:
                self._schedules[schedule_id]["status"] = SchedulerStatus.stopped
        
        thread = threading.Thread(target=schedule_loop, daemon=True)
        self._threads[schedule_id] = thread
        thread.start()
        
        return True
    
    def stop_schedule(self, schedule_id: str) -> bool:
        """
        停止定时任务
        
        Args:
            schedule_id: 调度ID
            
        Returns:
            是否停止成功
        """
        if schedule_id not in self._stop_events:
            return False
        
        self._stop_events[schedule_id].set()
        
        if schedule_id in self._schedules:
            self._schedules[schedule_id]["status"] = SchedulerStatus.stopped
        
        return True
    
    def get_schedule_status(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        获取定时任务状态
        
        Args:
            schedule_id: 调度ID
            
        Returns:
            任务状态信息
        """
        if schedule_id not in self._schedules:
            return None
        
        schedule = self._schedules[schedule_id]
        
        # 计算剩余时间
        remaining_seconds = 0
        if schedule["status"] == SchedulerStatus.waiting and schedule["next_run"]:
            remaining_seconds = max(0, int((schedule["next_run"] - datetime.now()).total_seconds()))
        
        return {
            "schedule_id": schedule_id,
            "crawler_type": schedule["crawler_type"],
            "interval_minutes": schedule["interval_minutes"],
            "status": schedule["status"],
            "next_run": schedule["next_run"].isoformat() if schedule["next_run"] else None,
            "last_run": schedule["last_run"].isoformat() if schedule["last_run"] else None,
            "remaining_seconds": remaining_seconds,
            "run_count": schedule["run_count"]
        }
    
    def get_all_schedules(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有定时任务状态
        
        Returns:
            所有任务状态
        """
        result = {}
        for schedule_id in self._schedules:
            status = self.get_schedule_status(schedule_id)
            if status:
                result[schedule_id] = status
        return result
    
    def is_running(self, schedule_id: str) -> bool:
        """
        检查任务是否在运行
        
        Args:
            schedule_id: 调度ID
            
        Returns:
            是否运行中
        """
        if schedule_id not in self._schedules:
            return False
        return self._schedules[schedule_id]["status"] in [SchedulerStatus.running, SchedulerStatus.waiting]


# 全局调度器实例
scheduler = CrawlerScheduler()
