#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试修复后的活动统计API"""
import requests
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api"

print("=== 测试修复后的API ===\n")

# 1. 登录获取token
print("1. 登录...")
response = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin123"})
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"[OK] 登录成功\n")
    headers = {"Authorization": f"Bearer {token}"}
else:
    print(f"[FAIL] 登录失败: {response.status_code}")
    exit(1)

# 2. 测试活动统计API
print("2. 测试活动统计API...")
response = requests.get(f"{BASE_URL}/activities/stats/summary", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"[OK] 活动统计API响应:")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    # 验证数据
    by_status = data.get('by_status', {})
    if len(by_status) == 3:  # 应该有3个状态
        print(f"\n[OK] 状态分类数量正确: {len(by_status)}个")
    else:
        print(f"\n[FAIL] 状态分类数量错误: 期待3个，实际{len(by_status)}个")

    if '已结束' in by_status and by_status['已结束'] == 3802:
        print(f"[OK] '已结束'状态数量正确: {by_status['已结束']}")
    else:
        print(f"[FAIL] '已结束'状态数量错误")

    if '其他状态' in by_status and by_status['其他状态'] == 408:
        print(f"[OK] '其他状态'状态数量正确: {by_status['其他状态']}")
    else:
        print(f"[FAIL] '其他状态'状态数量错误")

    if '特殊状态' in by_status and by_status['特殊状态'] == 1:
        print(f"[OK] '特殊状态'状态数量正确: {by_status['特殊状态']}")
    else:
        print(f"[FAIL] '特殊状态'状态数量错误")

    # 检查是否有重复的状态名
    status_names = list(by_status.keys())
    if len(status_names) == len(set(status_names)):
        print(f"\n[OK] 没有重复的状态名称")
    else:
        print(f"\n[FAIL] 存在重复的状态名称: {status_names}")
else:
    print(f"[FAIL] 活动统计API失败: {response.status_code} - {response.text}")

print("\n测试完成！")
