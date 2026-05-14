#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发送邮件脚本
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app.models import Student, NotificationType
from app.services.email_service import EmailService
from app.utils.email_template import render_new_activity_email

def main():
    db = SessionLocal()

    try:
        # 查询学生信息
        student_code = "20232818"
        student = db.query(Student).filter(Student.code == student_code).first()

        if not student:
            print(f"未找到学号为 {student_code} 的学生")
            return

        print(f"找到学生: {student.name}")
        print(f"邮箱: {student.email}")

        if not student.email:
            print("该学生没有设置邮箱!")
            return

        # 构造测试活动数据
        test_activity = {
            "act_id": 9999,
            "act_name": "【测试】Python编程技能培训",
            "class_name": "创新创业",
            "org_name": "数智维新工作室",
            "start_time": datetime(2025, 1, 15, 14, 0),
            "end_time": datetime(2025, 1, 15, 17, 0),
            "pitch_address": "信息楼A201",
            "job": 1,
            "introduce": "本次活动将介绍Python编程基础知识，包括数据类型、控制流程、函数定义等内容。欢迎感兴趣的同学报名参加！",
            "qq_groups": "123456789",
            "people_limit": 50,
            "enroll_end_time": datetime(2025, 1, 14, 23, 59),
            "college_name": "不限",
            "grade_name": "2023级"
        }

        # 渲染邮件内容
        html_content = render_new_activity_email(test_activity)
        subject = f"【二课通知】{test_activity['act_name']}可以报名了！"

        # 发送邮件 - 使用非测试模式实际发送
        email_service = EmailService(db, test_mode=False)

        print(f"\n正在发送邮件到: {student.email}")
        print(f"邮件主题: {subject}")

        result = email_service.send_email(
            to_email=student.email,
            subject=subject,
            html_content=html_content,
            act_id=test_activity["act_id"],
            student_code=student_code,
            email_type=NotificationType.NEW_ACTIVITY
        )

        if result:
            print("\n邮件发送成功!")
        else:
            print("\n邮件发送失败!")

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
