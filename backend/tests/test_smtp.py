#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试SMTP连接"""
import smtplib
from email.mime.text import MIMEText

# QQ邮箱配置
smtp_server = "smtp.qq.com"
smtp_port = 465
sender_email = "lcxlio@qq.com"
auth_code = "vxxzxmrcnzbvddde"

print("测试SMTP连接...")
print(f"服务器: {smtp_server}:{smtp_port}")
print(f"发件人: {sender_email}")

try:
    print("\n1. 连接SMTP服务器...")
    server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
    print("   连接成功!")

    print("\n2. 登录...")
    server.login(sender_email, auth_code)
    print("   登录成功!")

    print("\n3. 发送测试邮件...")
    msg = MIMEText("这是一封测试邮件", "plain", "utf-8")
    msg["From"] = sender_email
    msg["To"] = sender_email  # 发给自己
    msg["Subject"] = "SMTP测试"

    server.send_message(msg)
    print("   发送成功!")

    server.quit()
    print("\n测试完成，SMTP配置正常！")

except Exception as e:
    print(f"\n错误: {type(e).__name__}: {e}")
