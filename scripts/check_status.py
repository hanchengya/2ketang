import pymysql
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = pymysql.connect(host='10.5.80.8', user='root', password='123456', database='2ketang', charset='utf8mb4')
cursor = conn.cursor()

print("=== 活动状态分析 ===\n")

# 查看不同status和status_all的示例
cursor.execute("""
    SELECT act_id, name, status, status_all,
           LEFT(start_time, 10) as start_date,
           LEFT(end_time, 10) as end_date
    FROM activities
    WHERE status IN (0, 1, 2)
    LIMIT 15
""")

print("act_id | status | status_all | name                           | 开始日期   | 结束日期")
print("-------|--------|-----------|-------------------------------|-----------|----------")
for row in cursor.fetchall():
    act_id, name, status, status_all, start_date, end_date = row
    name_short = (name[:25] + '...') if len(name) > 25 else name
    print(f"{act_id:6} | {status:6} | {status_all:10} | {name_short:29} | {start_date or 'N/A':10} | {end_date or 'N/A':10}")

# 统计
print("\n=== 统计信息 ===")
cursor.execute("SELECT status, status_all, COUNT(*) FROM activities GROUP BY status, status_all ORDER BY status, status_all")
print("\nstatus | status_all | count")
print("-------|-----------|-------")
for status, status_all, count in cursor.fetchall():
    print(f"{status:6} | {status_all:10} | {count:6}")

conn.close()
