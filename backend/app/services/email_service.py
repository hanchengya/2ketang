#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件发送服务
"""
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import settings
from app.models import EmailLog, EmailStatus, NotificationType
from app.utils.email_template import (
    render_new_activity_email,
    render_sign_in_email,
    render_sign_out_email
)


class EmailService:
    """邮件发送服务"""

    def __init__(self, db: Session, test_mode: bool = None):
        """
        初始化邮件服务

        Args:
            db: 数据库会话
            test_mode: 测试模式（不实际发送邮件），默认使用配置文件设置
        """
        self.db = db
        self.test_mode = test_mode if test_mode is not None else settings.TEST_MODE
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.sender_email = settings.SENDER_EMAIL
        self.auth_code = settings.EMAIL_AUTH_CODE
        self.sender_name = settings.SENDER_NAME

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        act_id: int,
        student_code: str,
        email_type: NotificationType
    ) -> bool:
        """
        发送单封邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML格式的邮件内容
            act_id: 活动ID
            student_code: 学号
            email_type: 邮件类型

        Returns:
            是否发送成功
        """
        # 创建邮件日志记录
        email_log = EmailLog(
            act_id=act_id,
            recipient_email=to_email,
            student_code=student_code,
            email_type=email_type,
            subject=subject,
            status=EmailStatus.PENDING
        )
        self.db.add(email_log)
        self.db.commit()

        # 测试模式
        if self.test_mode:
            print(f"[测试模式] 发送邮件到: {to_email}")
            print(f"主题: {subject}")
            print(f"内容: {html_content[:200]}...")

            # 更新日志状态
            email_log.status = EmailStatus.SENT
            email_log.sent_at = datetime.now()
            self.db.commit()
            return True

        # 实际发送邮件
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f'{self.sender_name} <{self.sender_email}>'
            msg['To'] = to_email
            msg['Subject'] = subject

            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.auth_code)
                server.send_message(msg)

            # 更新日志状态
            email_log.status = EmailStatus.SENT
            email_log.sent_at = datetime.now()
            self.db.commit()

            print(f"[OK] 邮件发送成功: {to_email}")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"[X] 邮件发送失败: {to_email} - {error_msg}")

            # 更新日志状态
            email_log.status = EmailStatus.FAILED
            email_log.error_message = error_msg[:1000]  # 限制错误信息长度
            self.db.commit()

            return False

    def send_batch_emails(
        self,
        recipients: List[Dict[str, Any]],
        activity: Dict[str, Any],
        email_type: NotificationType
    ) -> Dict[str, int]:
        """
        批量发送邮件

        Args:
            recipients: 收件人列表，每个元素包含email和code字段
            activity: 活动信息字典
            email_type: 邮件类型

        Returns:
            发送统计字典，包含success_count和fail_count
        """
        success_count = 0
        fail_count = 0
        total = len(recipients)

        print(f"\n{'='*60}")
        print(f"开始批量发送邮件")
        print(f"收件人数量: {total}")
        print(f"邮件类型: {email_type.value}")
        print(f"测试模式: {'是' if self.test_mode else '否'}")
        print(f"{'='*60}\n")

        # 根据邮件类型选择模板
        if email_type == NotificationType.NEW_ACTIVITY:
            subject = f"【二课通知】{activity.get('act_name', '新活动')}可以报名了！"
            html_content = render_new_activity_email(activity)
        elif email_type == NotificationType.SIGN_IN:
            subject = f"【签到提醒】{activity.get('act_name', '活动')}开始签到了！"
            html_content = render_sign_in_email(activity)
        elif email_type == NotificationType.SIGN_OUT:
            subject = f"【签退提醒】{activity.get('act_name', '活动')}开始签退了！"
            html_content = render_sign_out_email(activity)
        else:
            print(f"未知的邮件类型: {email_type}")
            return {"success_count": 0, "fail_count": total}

        # 批量发送
        for i, recipient in enumerate(recipients, 1):
            email = recipient.get("email")
            code = recipient.get("code")

            if not email:
                print(f"[{i}/{total}] 学号 {code}: 邮箱为空，跳过")
                fail_count += 1
                continue

            print(f"[{i}/{total}] 发送到 {email} (学号: {code})...")

            success = self.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                act_id=activity.get("act_id"),
                student_code=code,
                email_type=email_type
            )

            if success:
                success_count += 1
            else:
                fail_count += 1

            # 每封邮件间隔，避免被限制
            if i < total:
                time.sleep(settings.EMAIL_DELAY)

            # 每10封显示一次进度
            if i % 10 == 0:
                print(f"\n进度: {i}/{total} ({i*100//total}%), 成功: {success_count}, 失败: {fail_count}\n")

        print(f"\n{'='*60}")
        print(f"批量发送完成!")
        print(f"    总计: {total} 封")
        print(f"    成功: {success_count} 封")
        print(f"    失败: {fail_count} 封")
        print(f"{'='*60}\n")

        return {
            "success_count": success_count,
            "fail_count": fail_count
        }


if __name__ == "__main__":
    # 测试代码
    from app.database import SessionLocal

    db = SessionLocal()
    email_service = EmailService(db, test_mode=True)

    # 测试发送单封邮件
    test_activity = {
        "act_id": 1,
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
        "grade_name": "不限"
    }

    result = email_service.send_email(
        to_email="test@example.com",
        subject="测试邮件",
        html_content=render_new_activity_email(test_activity),
        act_id=1,
        student_code="20232818",
        email_type=NotificationType.NEW_ACTIVITY
    )

    print(f"发送结果: {result}")
    db.close()
