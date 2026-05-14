#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加qq_groups字段到activity_details表
"""
from app.database import engine
from sqlalchemy import text

def add_qq_groups_field():
    """添加qq_groups字段"""
    sql = """
    ALTER TABLE activity_details
    ADD COLUMN qq_groups VARCHAR(500) COMMENT '活动QQ群号'
    """

    try:
        with engine.connect() as conn:
            # 先检查字段是否已存在
            check_sql = """
            SELECT COUNT(*) as cnt
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = '2ketang'
            AND TABLE_NAME = 'activity_details'
            AND COLUMN_NAME = 'qq_groups'
            """
            result = conn.execute(text(check_sql))
            exists = result.fetchone()[0] > 0

            if exists:
                print("qq_groups字段已存在")
            else:
                conn.execute(text(sql))
                conn.commit()
                print("成功添加qq_groups字段")
    except Exception as e:
        print(f"添加字段失败: {e}")

if __name__ == "__main__":
    add_qq_groups_field()
