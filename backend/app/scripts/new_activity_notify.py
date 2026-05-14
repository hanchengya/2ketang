#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本1：新活动报名通知
- 爬取"报名中"的活动及其详情
- 对比数据库找出新活动
- 根据活动要求的系部和年级给对应学生发送通知
- 只发送一次
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Activity, ActivityDetail, ActivityNotification, NotificationType
from app.services.notification_service import NotificationService
from app.crawlers.activity_crawler import crawl_activities
from app.crawlers.detail_crawler import crawl_activity_details
from app.crawlers.login import login_and_get_driver


class NewActivityNotifyScript:
    """新活动报名通知脚本"""

    def __init__(self, db: Session, test_mode: bool = False, task_id: str = None, task_manager = None):
        self.db = db
        self.test_mode = test_mode
        self.task_id = task_id
        self.task_manager = task_manager
        self.notification_service = NotificationService(db, test_mode)

    def log(self, message: str):
        """记录日志到任务管理器和控制台"""
        print(message)
        if self.task_id and self.task_manager:
            self.task_manager.append_log(self.task_id, self.db, message)

    def should_stop(self) -> bool:
        """检查是否应该停止"""
        if self.task_id and self.task_manager:
            return self.task_manager.should_stop(self.task_id)
        return False
    
    def get_existing_activity_ids(self) -> set:
        """获取数据库中已存在的活动ID"""
        activities = self.db.query(Activity.act_id).all()
        return set(a.act_id for a in activities)
    
    def get_notified_activity_ids(self) -> set:
        """获取已发送过新活动通知的活动ID"""
        notifications = self.db.query(ActivityNotification.act_id).filter(
            ActivityNotification.notification_type == NotificationType.NEW_ACTIVITY.value
        ).all()
        return set(n.act_id for n in notifications)
    
    def find_new_activities(self, crawled_activities: List[Dict]) -> List[Dict]:
        """
        找出新活动（数据库中不存在且未发送过通知的）
        
        Args:
            crawled_activities: 爬取到的活动列表
            
        Returns:
            新活动列表
        """
        existing_ids = self.get_existing_activity_ids()
        notified_ids = self.get_notified_activity_ids()
        
        new_activities = []
        for activity in crawled_activities:
            act_id = activity.get('act_id')
            if act_id and act_id not in existing_ids and act_id not in notified_ids:
                new_activities.append(activity)
        
        return new_activities
    
    def run(self) -> Dict[str, Any]:
        """
        运行脚本

        Returns:
            执行结果统计
        """
        self.log("=" * 50)
        self.log("新活动报名通知脚本启动")
        self.log(f"启动时间: {datetime.now()}")
        self.log("=" * 50)

        result = {
            "status": "success",
            "crawled_count": 0,
            "new_count": 0,
            "notified_count": 0,
            "success_count": 0,
            "fail_count": 0,
            "errors": []
        }

        driver = None
        try:
            # 检查是否应该停止
            if self.should_stop():
                self.log("任务被用户停止")
                result["status"] = "stopped"
                return result

            # 1. 登录并获取driver
            self.log("\n[1/4] 登录系统...")
            driver = login_and_get_driver()
            if not driver:
                result["status"] = "failed"
                result["errors"].append("登录失败")
                self.log("登录失败")
                return result
            self.log("登录成功")

            # 检查是否应该停止
            if self.should_stop():
                self.log("任务被用户停止")
                result["status"] = "stopped"
                return result

            # 2. 只爬取"报名中"的活动
            self.log("\n[2/4] 爬取报名中的活动...")
            activities = crawl_activities(
                driver,
                tabs=["报名中"],  # 只爬取报名中
                stop_check=self.should_stop
            )
            result["crawled_count"] = len(activities)
            self.log(f"爬取到 {len(activities)} 个报名中的活动")

            if not activities:
                self.log("没有找到报名中的活动")
                return result

            # 检查是否应该停止
            if self.should_stop():
                self.log("任务被用户停止")
                result["status"] = "stopped"
                return result

            # 3. 找出新活动
            self.log("\n[3/4] 对比数据库，筛选新活动...")
            new_activities = self.find_new_activities(activities)
            result["new_count"] = len(new_activities)
            self.log(f"发现 {len(new_activities)} 个新活动")

            if not new_activities:
                self.log("没有新活动需要通知")
                return result

            # 4. 爬取新活动的详情并发送通知
            self.log("\n[4/4] 爬取活动详情并发送通知...")
            for activity in new_activities:
                # 检查是否应该停止
                if self.should_stop():
                    self.log("任务被用户停止")
                    result["status"] = "stopped"
                    return result

                act_id = activity.get('act_id')
                act_name = activity.get('name', '未知活动')

                try:
                    # 爬取活动详情
                    self.log(f"\n处理活动: {act_name} (ID: {act_id})")
                    details = crawl_activity_details(
                        driver,
                        [act_id],
                        progress_callback=None,
                        stop_check=self.should_stop
                    )

                    if details:
                        detail = details[0]
                        # 发送通知
                        notify_result = self.notification_service.send_new_activity_notification(detail)

                        if notify_result.get("status") == "sent":
                            result["notified_count"] += 1
                            result["success_count"] += notify_result.get("success_count", 0)
                            result["fail_count"] += notify_result.get("fail_count", 0)
                            self.log(f"  -> 通知发送成功: {notify_result.get('success_count', 0)} 人")
                        else:
                            self.log(f"  -> 跳过: {notify_result.get('reason', 'unknown')}")
                    else:
                        self.log(f"  -> 未能获取活动详情")

                except Exception as e:
                    error_msg = f"处理活动 {act_id} 失败: {str(e)}"
                    self.log(f"  -> 错误: {error_msg}")
                    result["errors"].append(error_msg)

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            self.log(f"\n脚本执行错误: {e}")

        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

        self.log("\n" + "=" * 50)
        self.log("脚本执行完成")
        self.log(f"结束时间: {datetime.now()}")
        self.log(f"统计: 爬取{result['crawled_count']}个, 新活动{result['new_count']}个, "
              f"通知{result['notified_count']}个, 成功{result['success_count']}人, 失败{result['fail_count']}人")
        self.log("=" * 50)

        return result


def run_script(test_mode: bool = False) -> Dict[str, Any]:
    """运行脚本的入口函数"""
    db = SessionLocal()
    try:
        script = NewActivityNotifyScript(db, test_mode)
        return script.run()
    finally:
        db.close()


if __name__ == "__main__":
    result = run_script(test_mode=True)
    print(f"\n最终结果: {result}")
