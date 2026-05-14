#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细分析数据库中的活动状态"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.models import Activity
from sqlalchemy import func
from datetime import datetime

db = SessionLocal()

print("=== 活动状态详细分析 ===\n")

# 1. 统计 status 字段的分布
print("1. status 字段分布:")
status_counts = db.query(
    Activity.status,
    func.count(Activity.act_id).label('count')
).group_by(Activity.status).order_by(Activity.status).all()

for status, count in status_counts:
    print(f"  status={status}: {count}条")

# 2. 统计 status_all 字段的分布
print("\n2. status_all 字段分布:")
status_all_counts = db.query(
    Activity.status_all,
    func.count(Activity.act_id).label('count')
).group_by(Activity.status_all).order_by(Activity.status_all).all()

for status_all, count in status_all_counts:
    print(f"  status_all={status_all}: {count}条")

# 3. 查看不同status值的活动示例（包含时间信息）
print("\n3. 不同status值的活动示例:")
for status_val in [0, 1, 2]:
    activities = db.query(Activity).filter(Activity.status == status_val).limit(3).all()
    if activities:
        print(f"\n  status={status_val} 的示例:")
        for act in activities:
            now = datetime.now()
            start_time = datetime.strptime(act.start_time, '%Y-%m-%d %H:%M:%S') if act.start_time else None
            end_time = datetime.strptime(act.end_time, '%Y-%m-%d %H:%M:%S') if act.end_time else None

            time_status = "未知"
            if start_time and end_time:
                if now < start_time:
                    time_status = "未开始"
                elif start_time <= now <= end_time:
                    time_status = "进行中"
                else:
                    time_status = "已结束"

            print(f"    - act_id={act.act_id}, status_all={act.status_all}, 时间状态={time_status}")
            print(f"      开始: {act.start_time}, 结束: {act.end_time}")

# 4. status 和 status_all 的交叉分析
print("\n4. status 和 status_all 的交叉统计:")
cross_stats = db.query(
    Activity.status,
    Activity.status_all,
    func.count(Activity.act_id).label('count')
).group_by(Activity.status, Activity.status_all).order_by(Activity.status, Activity.status_all).all()

print("  status | status_all | count")
print("  -------|-----------|-------")
for status, status_all, count in cross_stats:
    print(f"  {status:6} | {status_all:10} | {count:6}")

db.close()
print("\n分析完成！")
