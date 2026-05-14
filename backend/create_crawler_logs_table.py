#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建爬虫日志表
"""
import pymysql
from app.config import settings

def create_crawler_logs_table():
    """创建爬虫日志表"""
    # 连接数据库
    conn = pymysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4'
    )

    try:
        cursor = conn.cursor()

        # 读取SQL文件
        with open('create_crawler_logs_table.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        # 执行SQL
        cursor.execute(sql)
        conn.commit()

        print("crawler_logs table created successfully!")

    except Exception as e:
        print(f"Failed to create table: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_crawler_logs_table()
