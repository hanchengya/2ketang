#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟浏览器完整流程测试
"""
import requests

BASE_URL = "http://localhost:5173/api"

def test_browser_flow():
    print("=" * 80)
    print("Simulating Browser Flow")
    print("=" * 80)

    # 创建session来保持cookies
    session = requests.Session()

    # 1. 登录
    print("\n1. Login...")
    login_resp = session.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    print(f"   Status: {login_resp.status_code}")

    if login_resp.status_code != 200:
        print(f"   ERROR: {login_resp.text}")
        return

    login_data = login_resp.json()
    token = login_data["access_token"]
    print(f"   Token: {token[:50]}...")

    # 设置Authorization header
    session.headers.update({"Authorization": f"Bearer {token}"})

    # 2. 访问Dashboard - 加载统计数据
    print("\n2. Dashboard - Loading stats...")

    print("   2.1 Activity Stats...")
    resp = session.get(f"{BASE_URL}/activities/stats/summary")
    print(f"       Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"       Response: {resp.text[:300]}")

    print("   2.2 Student Stats...")
    resp = session.get(f"{BASE_URL}/students/stats/summary")
    print(f"       Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"       Response: {resp.text[:300]}")

    print("   2.3 Notification Stats...")
    resp = session.get(f"{BASE_URL}/notifications/stats/summary")
    print(f"       Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"       Response: {resp.text[:300]}")

    # 3. 点击活动管理
    print("\n3. Click Activities Menu...")
    resp = session.get(f"{BASE_URL}/activities", params={"skip": 0, "limit": 20})
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Total: {data.get('total')}, Items: {len(data.get('items', []))}")
    else:
        print(f"   ERROR: {resp.text[:300]}")

    # 4. 点击学生管理
    print("\n4. Click Students Menu...")
    resp = session.get(f"{BASE_URL}/students", params={"skip": 0, "limit": 20})
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Total: {data.get('total')}, Items: {len(data.get('items', []))}")
    else:
        print(f"   ERROR: {resp.text[:300]}")

    # 5. 点击通知记录
    print("\n5. Click Notifications Menu...")
    resp = session.get(f"{BASE_URL}/notifications", params={"skip": 0, "limit": 20})
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Total: {data.get('total')}, Items: {len(data.get('items', []))}")
    else:
        print(f"   ERROR: {resp.text[:300]}")

    print("\n" + "=" * 80)
    print("Browser Flow Test Completed!")
    print("=" * 80)

if __name__ == '__main__':
    test_browser_flow()
