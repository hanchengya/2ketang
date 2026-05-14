#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本3：签退通知
- 爬取"进行中"的活动
- 对比发放学分列表中的签退时间
- 如果签退时间不为空，给列表中的学生发送签退通知
- 只发送一次
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Activity, ActivityParticipant, ActivityNotification, NotificationType, Student
from app.services.notification_service import NotificationService
from app.crawlers.activity_crawler import crawl_activities
from app.crawlers.participant_crawler import crawl_activity_participants
from app.crawlers.login import login_and_get_driver
from datetime import datetime as dt_datetime


class SignOutNotifyScript:
    """签退通知脚本"""

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

    def _timestamp_to_datetime(self, timestamp):
        """将时间戳转换为datetime"""
        if not timestamp:
            return None
        try:
            if isinstance(timestamp, (int, float)):
                if timestamp > 10000000000:
                    timestamp = timestamp / 1000
                return dt_datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # 处理逗号分隔的多个时间值，取第一个
                timestamp = timestamp.strip()
                if ',' in timestamp:
                    timestamp = timestamp.split(',')[0].strip()

                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                    try:
                        return dt_datetime.strptime(timestamp, fmt)
                    except:
                        continue
                # 最后尝试ISO格式
                return dt_datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return None
        return None

    def save_participants_to_db(self, act_id: int, participants: list):
        """保存参与者数据到数据库"""
        saved_count = 0
        for participant in participants:
            try:
                student_code = participant.get("code") or participant.get("studentCode")
                if not student_code:
                    continue

                existing = self.db.query(ActivityParticipant).filter(
                    ActivityParticipant.act_id == act_id,
                    ActivityParticipant.student_code == student_code
                ).first()

                sign_in_time = self._timestamp_to_datetime(
                    participant.get("inTime") or participant.get("signInTime") or
                    participant.get("sign_in_time") or participant.get("signinTime") or
                    participant.get("checkInTime")
                )
                sign_out_time = self._timestamp_to_datetime(
                    participant.get("outTime") or participant.get("signOutTime") or
                    participant.get("sign_out_time") or participant.get("signoutTime") or
                    participant.get("checkOutTime")
                )

                if existing:
                    existing.sign_in_time = sign_in_time
                    existing.sign_out_time = sign_out_time
                else:
                    new_participant = ActivityParticipant(
                        act_id=act_id,
                        student_code=student_code,
                        student_name=participant.get("name") or participant.get("studentName"),
                        sign_in_time=sign_in_time,
                        sign_out_time=sign_out_time,
                        credits=participant.get("credits")
                    )
                    self.db.add(new_participant)
                saved_count += 1
            except Exception as e:
                self.log(f"  -> 保存参与者失败: {e}")
        
        self.db.commit()
        return saved_count

    def get_notified_sign_out_ids(self) -> set:
        """获取已发送过签退通知的活动ID"""
        notifications = self.db.query(ActivityNotification.act_id).filter(
            ActivityNotification.notification_type == NotificationType.SIGN_OUT.value
        ).all()
        return set(n.act_id for n in notifications)
    
    def get_activity_participant_stats(self, act_id: int) -> Dict:
        """
        获取活动参与者统计信息
        
        Args:
            act_id: 活动ID
            
        Returns:
            统计信息字典
        """
        total = self.db.query(ActivityParticipant).filter(
            ActivityParticipant.act_id == act_id
        ).count()
        
        signed_in = self.db.query(ActivityParticipant).filter(
            ActivityParticipant.act_id == act_id,
            ActivityParticipant.sign_in_time.isnot(None)
        ).count()
        
        signed_out = self.db.query(ActivityParticipant).filter(
            ActivityParticipant.act_id == act_id,
            ActivityParticipant.sign_out_time.isnot(None)
        ).count()
        
        return {
            "total": total,
            "signed_in": signed_in,
            "waiting_sign_in": total - signed_in,
            "signed_out": signed_out,
            "waiting_sign_out": signed_in - signed_out
        }

    def get_participants_with_sign_out(self, act_id: int) -> List[Dict]:
        """
        获取有签退时间的参与者
        
        Args:
            act_id: 活动ID
            
        Returns:
            有签退时间的参与者列表
        """
        participants = self.db.query(ActivityParticipant).filter(
            ActivityParticipant.act_id == act_id,
            ActivityParticipant.sign_out_time.isnot(None)
        ).all()
        
        result = []
        for p in participants:
            student = self.db.query(Student).filter(
                Student.code == p.student_code
            ).first()
            
            if student and student.email:
                result.append({
                    "code": p.student_code,
                    "name": p.student_name or (student.name if student else ""),
                    "email": student.email,
                    "sign_out_time": p.sign_out_time
                })
        
        return result
    
    def run(self) -> Dict[str, Any]:
        """
        运行脚本

        Returns:
            执行结果统计
        """
        self.log("=" * 50)
        self.log("签退通知脚本启动")
        self.log(f"启动时间: {datetime.now()}")
        self.log("=" * 50)

        result = {
            "status": "success",
            "crawled_count": 0,
            "checked_count": 0,
            "activities_checked": 0,
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

            # 2. 只爬取"进行中"的活动
            self.log("\n[2/4] 爬取进行中的活动...")
            activities = crawl_activities(
                driver,
                tabs=["进行中"],  # 只爬取进行中
                stop_check=self.should_stop
            )
            result["crawled_count"] = len(activities)
            self.log(f"爬取到 {len(activities)} 个进行中的活动")

            if not activities:
                self.log("没有找到进行中的活动")
                return result

            # 3. 获取已发送过签退通知的活动ID
            notified_ids = self.get_notified_sign_out_ids()
            self.log(f"已有 {len(notified_ids)} 个活动发送过签退通知")

            # 4. 遍历活动，爬取参与者并检查签退时间
            self.log("\n[3/4] 爬取参与者信息...")
            for activity in activities:
                # 检查是否应该停止
                if self.should_stop():
                    self.log("任务被用户停止")
                    result["status"] = "stopped"
                    return result

                act_id = activity.get('act_id')
                act_name = activity.get('name', '未知活动')

                # 跳过已发送过通知的活动
                if act_id in notified_ids:
                    self.log(f"活动 {act_name} (ID: {act_id}) 已发送过签退通知，跳过")
                    continue

                result["activities_checked"] += 1
                result["checked_count"] += 1

                try:
                    self.log(f"\n检查活动: {act_name} (ID: {act_id})")

                    # 爬取参与者信息（单个活动）
                    crawl_result = crawl_activity_participants(driver, act_id)
                    
                    # 保存参与者数据到数据库
                    if crawl_result and crawl_result.get("participants"):
                        saved = self.save_participants_to_db(act_id, crawl_result["participants"])
                        self.log(f"  -> 已保存 {saved} 条参与者记录到数据库")

                    # 获取参与者统计信息
                    stats = self.get_activity_participant_stats(act_id)
                    self.log(f"  -> 参与者: {stats['total']}人, 已签到: {stats['signed_in']}人, 等待签到: {stats['waiting_sign_in']}人")
                    self.log(f"  -> 已签退: {stats['signed_out']}人, 等待签退: {stats['waiting_sign_out']}人")

                    # 从数据库获取有签退时间的参与者
                    participants = self.get_participants_with_sign_out(act_id)

                    if participants:
                        self.log(f"  -> 找到 {len(participants)} 个有签退记录的参与者")

                        # 构建活动信息
                        activity_info = {
                            "act_id": act_id,
                            "act_name": act_name,
                            "name": act_name
                        }

                        # 发送签退通知
                        notify_result = self.notification_service.send_sign_out_notification(
                            activity_info,
                            participants
                        )

                        if notify_result.get("status") == "sent":
                            result["notified_count"] += 1
                            result["success_count"] += notify_result.get("success_count", 0)
                            result["fail_count"] += notify_result.get("fail_count", 0)
                            self.log(f"  -> 通知发送成功: {notify_result.get('success_count', 0)} 人")
                        else:
                            self.log(f"  -> 跳过: {notify_result.get('reason', 'unknown')}")
                    else:
                        self.log(f"  -> 暂无签退记录")

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
        self.log(f"统计: 爬取{result['crawled_count']}个活动, 检查{result['activities_checked']}个, "
              f"通知{result['notified_count']}个, 成功{result['success_count']}人, 失败{result['fail_count']}人")
        self.log("=" * 50)

        return result


def run_script(test_mode: bool = False) -> Dict[str, Any]:
    """运行脚本的入口函数"""
    db = SessionLocal()
    try:
        script = SignOutNotifyScript(db, test_mode)
        return script.run()
    finally:
        db.close()


if __name__ == "__main__":
    result = run_script(test_mode=True)
    print(f"\n最终结果: {result}")
