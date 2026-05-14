#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查students表结构
"""
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': '10.5.80.8',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': '2ketang',
    'charset': 'utf8mb4'
}

def check_students_table():
    """检查students表结构"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DESCRIBE students")
        results = cursor.fetchall()

        print("Students table structure:")
        print("-" * 80)
        for row in results:
            print(f"{row[0]:<30} {row[1]:<20} {row[2]:<10} {row[3]:<10}")
        print("-" * 80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_students_table()
