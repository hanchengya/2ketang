#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：给有邮箱的学生发送三种通知
使用完整的邮件模板发送
"""
import sys
import os
import io
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入邮件模板
from app.utils.email_template import render_new_activity_email, render_sign_in_email, render_sign_out_email

# SMTP配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = "lcxlio@qq.com"
AUTH_CODE = "vxxzxmrcnzbvddde"
SENDER_NAME = "数智维新工作室"


def send_email(to_email, subject, html_content, max_retries=3):
    """直接发送邮件（带重试机制）"""
    for attempt in range(max_retries):
        try:
            msg = MIMEMultipart('alternative')
            # 正确编码中文发件人名称
            msg['From'] = f'{Header(SENDER_NAME, "utf-8").encode()} <{SENDER_EMAIL}>'
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')

            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=60)
            server.login(SENDER_EMAIL, AUTH_CODE)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            server.quit()

            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"   第{attempt + 1}次发送失败，正在重试...")
                time.sleep(3)
            else:
                print(f"   发送失败: {e}")
                return False


def main():
    print("=" * 60)
    print("测试通知发送脚本 (使用完整模板)")
    print("发送时间:", datetime.now())
    print("=" * 60)

    # 有邮箱的两个学生
    test_students = [
        {"code": "20232818", "name": "测试学生1", "email": "19161931205@163.com"},
        {"code": "20202945", "name": "测试学生2", "email": "2029871922@qq.com"},
    ]

    # 模拟完整的活动信息（包含12个字段）
    test_activity = {
        "act_id": 9999,
        "act_name": "【测试】Python编程技能培训",
        "class_name": "创新创业",
        "org_name": "数智维新工作室",
        "start_time": datetime(2025, 1, 15, 14, 0),
        "end_time": datetime(2025, 1, 15, 17, 0),
        "pitch_address": "信息楼A201",
        "job": 1,  # 需要提交作业
        "introduce": "本次活动将介绍Python编程基础知识，包括数据类型、控制流程、函数定义等内容。欢迎感兴趣的同学报名参加！活动结束后需提交学习心得。",
        "qq_groups": "123456789",
        "people_limit": 50,
        "enroll_end_time": datetime(2025, 1, 14, 23, 59),
        "college_name": "不限",
        "grade_name": "2023级、2024级"
    }

    success_count = 0
    fail_count = 0

    for student in test_students:
        print("\n" + "=" * 60)
        print("正在给", student['name'], "(", student['email'], ") 发送通知...")
        print("=" * 60)

        # 1. 发送新活动通知（使用完整12字段模板）
        print("\n[1/3] 发送新活动通知（完整模板）...")
        subject1 = f"【二课通知】{test_activity['act_name']}可以报名了！"
        content1 = render_new_activity_email(test_activity)
        if send_email(student['email'], subject1, content1):
            print("   [OK] 新活动通知发送成功")
            success_count += 1
        else:
            fail_count += 1
        time.sleep(2)  # 添加延迟避免被限制

        # 2. 发送签到通知
        print("\n[2/3] 发送签到通知...")
        subject2 = f"【签到提醒】{test_activity['act_name']}"
        content2 = render_sign_in_email(test_activity)
        if send_email(student['email'], subject2, content2):
            print("   [OK] 签到通知发送成功")
            success_count += 1
        else:
            fail_count += 1
        time.sleep(2)  # 添加延迟避免被限制

        # 3. 发送签退通知
        print("\n[3/3] 发送签退通知...")
        subject3 = f"【签退提醒】{test_activity['act_name']}"
        content3 = render_sign_out_email(test_activity)
        if send_email(student['email'], subject3, content3):
            print("   [OK] 签退通知发送成功")
            success_count += 1
        else:
            fail_count += 1

        print("\n" + student['name'] + " 的所有通知发送完成！")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("成功:", success_count, "封")
    print("失败:", fail_count, "封")
    print("=" * 60)


if __name__ == "__main__":
    main()
