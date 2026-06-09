#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新admin用户密码
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

# 新的密码哈希 (admin123)
NEW_PASSWORD_HASH = '$2b$12$5BJACBReXMmIVuAwCCgjpOFhGK48Radr3k/dgCou9HW2DkMpZBdAC'

def update_admin_password():
    """更新admin用户密码"""
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 更新密码
        sql = "UPDATE users SET password_hash = %s WHERE username = 'admin'"
        cursor.execute(sql, (NEW_PASSWORD_HASH,))
        conn.commit()

        print(f"[OK] Password updated successfully, rows affected: {cursor.rowcount}")

        # 验证更新
        cursor.execute("SELECT username, role, LEFT(password_hash, 30) as password_prefix FROM users WHERE username = 'admin'")
        result = cursor.fetchone()
        if result:
            print(f"[OK] Verification successful:")
            print(f"  Username: {result[0]}")
            print(f"  Role: {result[1]}")
            print(f"  Password hash prefix: {result[2]}...")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[FAIL] Update failed: {e}")

if __name__ == '__main__':
    update_admin_password()
