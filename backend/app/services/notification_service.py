#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知服务
协调爬虫、学生匹配、邮件发送的完整流程
"""
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import ActivityNotification, NotificationType
from app.services.email_service import EmailService
from app.services.student_matcher import match_students_for_activity


class NotificationService:
    """通知服务"""

    def __init__(self, db: Session, test_mode: bool = None):
        """
        初始化通知服务

        Args:
            db: 数据库会话
            test_mode: 测试模式
        """
        self.db = db
        self.email_service = EmailService(db, test_mode)

    def check_notification_sent(
        self,
        act_id: int,
        notification_type: NotificationType
    ) -> bool:
        """
        检查活动是否已发送通知

        Args:
            act_id: 活动ID
            notification_type: 通知类型

        Returns:
            是否已发送
        """
        notification = self.db.query(ActivityNotification).filter(
            ActivityNotification.act_id == act_id,
            ActivityNotification.notification_type == notification_type
        ).first()

        return notification is not None

    def record_notification(
        self,
        act_id: int,
        notification_type: NotificationType,
        recipient_count: int,
        success_count: int,
        fail_count: int
    ) -> ActivityNotification:
        """
        记录通知发送状态

        Args:
            act_id: 活动ID
            notification_type: 通知类型
            recipient_count: 接收人数
            success_count: 成功发送数
            fail_count: 失败发送数

        Returns:
            通知记录
        """
        notification = ActivityNotification(
            act_id=act_id,
            notification_type=notification_type,
            sent_at=datetime.now(),
            recipient_count=recipient_count,
            success_count=success_count,
            fail_count=fail_count
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        return notification

    def send_new_activity_notification(
        self,
        activity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送新活动通知

        Args:
            activity: 活动信息字典

        Returns:
            发送结果统计
        """
        act_id = activity.get("act_id")
        act_name = activity.get("act_name", "未知活动")

        print(f"\n{'='*60}")
        print(f"发送新活动通知: {act_name} (ID: {act_id})")
        print(f"{'='*60}")

        # 检查是否已发送
        if self.check_notification_sent(act_id, NotificationType.NEW_ACTIVITY):
            print("该活动已发送过通知，跳过")
            return {
                "status": "skipped",
                "reason": "already_sent",
                "success_count": 0,
                "fail_count": 0
            }

        # 检查是否包含"后台导入"
        if activity.get("is_backend_import"):
            print("检测到'后台导入'，跳过此活动")
            return {
                "status": "skipped",
                "reason": "backend_import",
                "success_count": 0,
                "fail_count": 0
            }

        # 匹配学生
        students = match_students_for_activity(self.db, activity)

        if not students:
            print("没有匹配到符合条件的学生")
            return {
                "status": "skipped",
                "reason": "no_students",
                "success_count": 0,
                "fail_count": 0
            }

        # 批量发送邮件
        result = self.email_service.send_batch_emails(
            recipients=students,
            activity=activity,
            email_type=NotificationType.NEW_ACTIVITY
        )

        # 记录通知
        self.record_notification(
            act_id=act_id,
            notification_type=NotificationType.NEW_ACTIVITY,
            recipient_count=len(students),
            success_count=result["success_count"],
            fail_count=result["fail_count"]
        )

        return {
            "status": "sent",
            "success_count": result["success_count"],
            "fail_count": result["fail_count"],
            "recipient_count": len(students)
        }

    def send_sign_in_notification(
        self,
        activity: Dict[str, Any],
        participants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        发送签到提醒通知

        Args:
            activity: 活动信息字典
            participants: 参与者列表

        Returns:
            发送结果统计
        """
        act_id = activity.get("act_id")
        act_name = activity.get("act_name", "未知活动")

        print(f"\n{'='*60}")
        print(f"发送签到提醒: {act_name} (ID: {act_id})")
        print(f"{'='*60}")

        # 检查是否已发送
        if self.check_notification_sent(act_id, NotificationType.SIGN_IN):
            print("该活动已发送过签到提醒，跳过")
            return {
                "status": "skipped",
                "reason": "already_sent",
                "success_count": 0,
                "fail_count": 0
            }

        # 准备收件人列表（从参与者中提取）
        recipients = []
        for participant in participants:
            student_code = participant.get("code") or participant.get("student_code")
            if student_code:
                # 从数据库查询学生邮箱
                from app.models import Student
                student = self.db.query(Student).filter(
                    Student.code == student_code
                ).first()
                if student and student.email:
                    recipients.append({
                        "code": student.code,
                        "name": student.name,
                        "email": student.email
                    })

        if not recipients:
            print("没有找到有邮箱的参与者")
            return {
                "status": "skipped",
                "reason": "no_recipients",
                "success_count": 0,
                "fail_count": 0
            }

        # 批量发送邮件
        result = self.email_service.send_batch_emails(
            recipients=recipients,
            activity=activity,
            email_type=NotificationType.SIGN_IN
        )

        # 记录通知
        self.record_notification(
            act_id=act_id,
            notification_type=NotificationType.SIGN_IN,
            recipient_count=len(recipients),
            success_count=result["success_count"],
            fail_count=result["fail_count"]
        )

        return {
            "status": "sent",
            "success_count": result["success_count"],
            "fail_count": result["fail_count"],
            "recipient_count": len(recipients)
        }

    def send_sign_out_notification(
        self,
        activity: Dict[str, Any],
        participants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        发送签退提醒通知

        Args:
            activity: 活动信息字典
            participants: 参与者列表

        Returns:
            发送结果统计
        """
        act_id = activity.get("act_id")
        act_name = activity.get("act_name", "未知活动")

        print(f"\n{'='*60}")
        print(f"发送签退提醒: {act_name} (ID: {act_id})")
        print(f"{'='*60}")

        # 检查是否已发送
        if self.check_notification_sent(act_id, NotificationType.SIGN_OUT):
            print("该活动已发送过签退提醒，跳过")
            return {
                "status": "skipped",
                "reason": "already_sent",
                "success_count": 0,
                "fail_count": 0
            }

        # 准备收件人列表（从参与者中提取）
        recipients = []
        for participant in participants:
            student_code = participant.get("code") or participant.get("student_code")
            if student_code:
                # 从数据库查询学生邮箱
                from app.models import Student
                student = self.db.query(Student).filter(
                    Student.code == student_code
                ).first()
                if student and student.email:
                    recipients.append({
                        "code": student.code,
                        "name": student.name,
                        "email": student.email
                    })

        if not recipients:
            print("没有找到有邮箱的参与者")
            return {
                "status": "skipped",
                "reason": "no_recipients",
                "success_count": 0,
                "fail_count": 0
            }

        # 批量发送邮件
        result = self.email_service.send_batch_emails(
            recipients=recipients,
            activity=activity,
            email_type=NotificationType.SIGN_OUT
        )

        # 记录通知
        self.record_notification(
            act_id=act_id,
            notification_type=NotificationType.SIGN_OUT,
            recipient_count=len(recipients),
            success_count=result["success_count"],
            fail_count=result["fail_count"]
        )

        return {
            "status": "sent",
            "success_count": result["success_count"],
            "fail_count": result["fail_count"],
            "recipient_count": len(recipients)
        }


if __name__ == "__main__":
    # 测试代码
    from app.database import SessionLocal
    from datetime import datetime

    db = SessionLocal()
    notification_service = NotificationService(db, test_mode=True)

    # 测试新活动通知
    test_activity = {
        "act_id": 9999,
        "act_name": "测试活动",
        "class_name": "测试分类",
        "org_name": "测试主办方",
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "pitch_address": "测试地点",
        "job": 0,
        "introduce": "这是一个测试活动",
        "qq_groups": "123456789",
        "people_limit": 100,
        "enroll_end_time": datetime.now(),
        "college_name": "不限",
        "grade_name": "不限",
        "is_backend_import": False
    }

    result = notification_service.send_new_activity_notification(test_activity)
    print(f"\n发送结果: {result}")

    db.close()
