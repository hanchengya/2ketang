#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试邮件日志API"""
import sys
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.models import EmailLog
from app.api.deps import get_db
from app.api.notifications import get_email_logs
from sqlalchemy.orm import Session

# 直接测试函数
db = SessionLocal()

try:
    print("测试邮件日志查询...")

    # 模拟API调用
    result = {
        'skip': 0,
        'limit': 20,
        'status': None,
        'student_code': None,
        'recipient_email': None
    }

    # 查询
    query = db.query(EmailLog)
    total = query.count()

    print(f"邮件总数: {total}")

    if total > 0:
        logs = query.order_by(EmailLog.created_at.desc()).limit(20).all()
        print(f"成功查询到 {len(logs)} 条记录")

        for log in logs[:3]:
            print(f"\n记录 {log.id}:")
            print(f"  - email: {log.recipient_email}")
            print(f"  - status: {log.status} (type: {type(log.status)})")
            print(f"  - email_type: {log.email_type} (type: {type(log.email_type)})")
    else:
        print("数据库中没有邮件日志")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
