#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据完整性
"""

import pymysql

DB_CONFIG = {
    'host': '10.5.80.8',
    'user': 'root',
    'password': '123456',
    'database': '2ketang',
    'charset': 'utf8mb4'
}

def check_data():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 总数
    cursor.execute("SELECT COUNT(*) FROM students")
    total = cursor.fetchone()[0]
    print(f"数据库总记录数: {total}")
    
    # ID范围
    cursor.execute("SELECT MIN(id), MAX(id) FROM students")
    min_id, max_id = cursor.fetchone()
    print(f"ID范围: {min_id} - {max_id}")
    
    # 按年级统计
    print("\n按年级统计:")
    cursor.execute("SELECT grade_name, COUNT(*) as cnt FROM students GROUP BY grade_name ORDER BY grade_name")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 条")
    
    # 按院系统计
    print("\n按院系统计:")
    cursor.execute("SELECT college_name, COUNT(*) as cnt FROM students GROUP BY college_name ORDER BY cnt DESC")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 条")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_data()
