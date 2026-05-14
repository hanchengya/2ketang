#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查数据库数据"""
import sys
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.models import Activity, ActivityNotification, EmailLog
from sqlalchemy import func

db = SessionLocal()

print("=== 数据库数据统计 ===\n")

# 活动统计
total_activities = db.query(Activity).count()
print(f"活动总数: {total_activities}")

# 按状态统计活动
status_counts = db.query(
    Activity.status,
    func.count(Activity.act_id).label('count')
).group_by(Activity.status).all()

status_map = {
    2: '待审核',
    4: '报名中',
    6: '进行中',
    8: '已结束'
}

print("按状态分类:")
for status, count in status_counts:
    status_name = status_map.get(status, f'状态{status}')
    print(f"  - {status_name}: {count}")

# 通知统计
total_notifications = db.query(ActivityNotification).count()
print(f"\n通知总数: {total_notifications}")

# 邮件统计
total_emails = db.query(EmailLog).count()
sent_emails = db.query(EmailLog).filter(EmailLog.status == "sent").count()
failed_emails = db.query(EmailLog).filter(EmailLog.status == "failed").count()
pending_emails = db.query(EmailLog).filter(EmailLog.status == "pending").count()

print(f"邮件总数: {total_emails}")
print(f"  - 已发送: {sent_emails}")
print(f"  - 失败: {failed_emails}")
print(f"  - 待发送: {pending_emails}")

db.close()
print("\n数据库检查完成！")
