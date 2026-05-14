#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试活动统计API的实际返回数据"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.models import Activity
from sqlalchemy import func

db = SessionLocal()

print("=== 测试活动统计API ===\n")

# 总活动数
total = db.query(Activity).count()
print(f"活动总数: {total}")

# 按状态分组统计
status_counts = db.query(
    Activity.status,
    func.count(Activity.act_id).label('count')
).group_by(Activity.status).all()

# 状态名称映射
status_map = {
    2: '待审核',
    4: '报名中',
    6: '进行中',
    8: '已结束'
}

# 构建按状态分类的统计
by_status = {}
print("\n按状态分组:")
for status, count in status_counts:
    status_name = status_map.get(status, f'状态{status}')
    by_status[status_name] = count
    print(f"  {status} -> {status_name}: {count}")

# 模拟API返回
response = {
    "total": total,
    "by_status": by_status
}

print(f"\nAPI返回的数据:")
import json
print(json.dumps(response, ensure_ascii=False, indent=2))

db.close()
