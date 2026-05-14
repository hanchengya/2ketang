#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理卡住的任务"""
import pymysql

conn = pymysql.connect(
    host='10.5.80.8',
    port=3306,
    user='root',
    password='123456',
    database='2ketang'
)
cursor = conn.cursor()
cursor.execute("UPDATE crawler_logs SET status = 'failed', finished_at = NOW() WHERE status = 'running'")
affected = cursor.rowcount
conn.commit()
cursor.close()
conn.close()
print(f'已修复 {affected} 个卡住的任务')
