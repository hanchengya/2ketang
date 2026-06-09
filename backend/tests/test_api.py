#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API认证
"""
import requests

BASE_URL = "http://localhost:8000/api"

# 1. 登录获取token
print("1. Testing login...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin", "password": "admin123"}
)
print(f"Login status: {login_response.status_code}")
if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"Token: {token[:50]}...")
else:
    print(f"Login failed: {login_response.text}")
    exit(1)

# 2. 测试学生列表API
print("\n2. Testing students API...")
headers = {"Authorization": f"Bearer {token}"}
students_response = requests.get(
    f"{BASE_URL}/students",
    headers=headers,
    params={"page": 1, "page_size": 10}
)
print(f"Students API status: {students_response.status_code}")
if students_response.status_code != 200:
    print(f"Error: {students_response.text}")

# 3. 测试活动列表API
print("\n3. Testing activities API...")
activities_response = requests.get(
    f"{BASE_URL}/activities",
    headers=headers,
    params={"page": 1, "page_size": 10}
)
print(f"Activities API status: {activities_response.status_code}")
if activities_response.status_code != 200:
    print(f"Error: {activities_response.text}")

# 4. 测试通知列表API
print("\n4. Testing notifications API...")
notifications_response = requests.get(
    f"{BASE_URL}/notifications",
    headers=headers,
    params={"page": 1, "page_size": 10}
)
print(f"Notifications API status: {notifications_response.status_code}")
if notifications_response.status_code != 200:
    print(f"Error: {notifications_response.text}")

print("\nAll tests completed!")
