#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证修复后的查询"""
import sys
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.models import EmailLog
from app.models.notification import EmailStatus

db = SessionLocal()

print("=== 验证邮件状态查询 ===\n")

# 使用枚举值查询
sent_count = db.query(EmailLog).filter(EmailLog.status == EmailStatus.SENT).count()
failed_count = db.query(EmailLog).filter(EmailLog.status == EmailStatus.FAILED).count()
pending_count = db.query(EmailLog).filter(EmailLog.status == EmailStatus.PENDING).count()

print(f"使用枚举值查询:")
print(f"  - 已发送: {sent_count}")
print(f"  - 失败: {failed_count}")
print(f"  - 待发送: {pending_count}")

# 检查EmailStatus枚举的值
print(f"\nEmailStatus枚举值:")
print(f"  - SENT: '{EmailStatus.SENT.value}'")
print(f"  - FAILED: '{EmailStatus.FAILED.value}'")
print(f"  - PENDING: '{EmailStatus.PENDING.value}'")

# 查看数据库中实际的状态值
sample_emails = db.query(EmailLog).limit(5).all()
print(f"\n数据库中的实际状态值:")
for email in sample_emails:
    print(f"  - ID {email.id}: status = '{email.status}' (type: {type(email.status).__name__})")

db.close()
print("\n验证完成！")
