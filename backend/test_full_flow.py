#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试登录和各个页面的API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_full_flow():
    print("=" * 80)
    print("Testing Full Flow")
    print("=" * 80)

    # 1. 登录
    print("\n1. Testing Login...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    print(f"   Status: {login_response.status_code}")

    if login_response.status_code != 200:
        print(f"   ERROR: {login_response.text}")
        return False

    login_data = login_response.json()
    token = login_data["access_token"]
    print(f"   Token: {token[:50]}...")
    print(f"   Username: {login_data['username']}")
    print(f"   Role: {login_data['role']}")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. 测试Dashboard统计API
    print("\n2. Testing Dashboard Stats APIs...")

    # 2.1 Activity Stats
    print("   2.1 Activity Stats...")
    resp = requests.get(f"{BASE_URL}/activities/stats/summary", headers=headers)
    print(f"       Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"       ERROR: {resp.text[:200]}")

    # 2.2 Student Stats
    print("   2.2 Student Stats...")
    resp = requests.get(f"{BASE_URL}/students/stats/summary", headers=headers)
    print(f"       Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"       ERROR: {resp.text[:200]}")

    # 2.3 Notification Stats
    print("   2.3 Notification Stats...")
    resp = requests.get(f"{BASE_URL}/notifications/stats/summary", headers=headers)
    print(f"       Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"       ERROR: {resp.text[:200]}")

    # 3. 测试活动列表
    print("\n3. Testing Activities List...")
    resp = requests.get(
        f"{BASE_URL}/activities",
        headers=headers,
        params={"skip": 0, "limit": 10}
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Total: {data.get('total', 0)}")
        print(f"   Items: {len(data.get('items', []))}")
    else:
        print(f"   ERROR: {resp.text[:200]}")

    # 4. 测试学生列表
    print("\n4. Testing Students List...")
    resp = requests.get(
        f"{BASE_URL}/students",
        headers=headers,
        params={"skip": 0, "limit": 10}
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Total: {data.get('total', 0)}")
        print(f"   Items: {len(data.get('items', []))}")
        if data.get('items'):
            first_student = data['items'][0]
            print(f"   First student: {first_student.get('name')} ({first_student.get('code')})")
    else:
        print(f"   ERROR: {resp.text[:200]}")

    # 5. 测试通知列表
    print("\n5. Testing Notifications List...")
    resp = requests.get(
        f"{BASE_URL}/notifications",
        headers=headers,
        params={"skip": 0, "limit": 10}
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Total: {data.get('total', 0)}")
        print(f"   Items: {len(data.get('items', []))}")
    else:
        print(f"   ERROR: {resp.text[:200]}")

    # 6. 测试邮件日志
    print("\n6. Testing Email Logs...")
    resp = requests.get(
        f"{BASE_URL}/notifications/email-logs",
        headers=headers,
        params={"skip": 0, "limit": 10}
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Total: {data.get('total', 0)}")
        print(f"   Items: {len(data.get('items', []))}")
    else:
        print(f"   ERROR: {resp.text[:200]}")

    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)
    return True

if __name__ == '__main__':
    test_full_flow()
