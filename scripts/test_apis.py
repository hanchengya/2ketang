#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试修复后的API"""
import requests
import json
import sys
import io

# 设置stdout为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api"

# 1. 登录获取token
print("1. 测试登录...")
login_data = {
    "username": "admin",
    "password": "admin123"
}
response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"[OK] 登录成功，获取到token: {token[:20]}...")
    headers = {"Authorization": f"Bearer {token}"}
else:
    print(f"[FAIL] 登录失败: {response.status_code} - {response.text}")
    exit(1)

# 2. 测试活动统计API
print("\n2. 测试活动统计API...")
response = requests.get(f"{BASE_URL}/activities/stats/summary", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"[OK] 活动统计API成功")
    print(f"  - 活动总数: {data.get('total', 0)}")
    print(f"  - 按状态分类: {data.get('by_status', {})}")
else:
    print(f"[FAIL] 活动统计API失败: {response.status_code} - {response.text}")

# 3. 测试通知统计API
print("\n3. 测试通知统计API...")
response = requests.get(f"{BASE_URL}/notifications/stats/summary", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"[OK] 通知统计API成功")
    print(f"  - 通知总数: {data.get('total', 0)}")
    print(f"  - 已发送: {data.get('sent_count', 0)}")
    print(f"  - 待发送: {data.get('pending_count', 0)}")
    print(f"  - 失败: {data.get('failed_count', 0)}")
    print(f"  - 最近通知数: {len(data.get('recent_notifications', []))}")
else:
    print(f"[FAIL] 通知统计API失败: {response.status_code} - {response.text}")

# 4. 测试邮件日志API
print("\n4. 测试邮件日志API...")
response = requests.get(f"{BASE_URL}/notifications/email-logs?skip=0&limit=20", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"[OK] 邮件日志API成功")
    print(f"  - 总记录数: {data.get('total', 0)}")
    print(f"  - 返回记录数: {len(data.get('items', []))}")
else:
    print(f"[FAIL] 邮件日志API失败: {response.status_code} - {response.text}")

# 5. 测试通知列表API（包含act_name）
print("\n5. 测试通知列表API...")
response = requests.get(f"{BASE_URL}/notifications/?skip=0&limit=5", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"[OK] 通知列表API成功")
    print(f"  - 总记录数: {data.get('total', 0)}")
    items = data.get('items', [])
    if items:
        print(f"  - 第一条记录的act_name: {items[0].get('act_name', '未找到')}")
else:
    print(f"[FAIL] 通知列表API失败: {response.status_code} - {response.text}")

print("\n测试完成！")
