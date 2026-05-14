#!/usr/bin/env python3
import pymysql

conn = pymysql.connect(host="10.5.80.8", port=3306, user="root", password="123456", database="2ketang")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM students WHERE email IS NOT NULL AND LENGTH(email) > 0")
with_email = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM students")
total = cursor.fetchone()[0]

print(f"学生总数: {total}")
print(f"有邮箱的学生: {with_email}")
print(f"无邮箱的学生: {total - with_email}")

# 查看几个有邮箱的学生示例
cursor.execute("SELECT code, name, email FROM students WHERE email IS NOT NULL AND LENGTH(email) > 0 LIMIT 5")
print("\n有邮箱的学生示例:")
for row in cursor.fetchall():
    print(f"  {row[0]} - {row[1]} - {row[2]}")

conn.close()
