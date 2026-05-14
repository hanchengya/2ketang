#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""
import pymysql
import sys

# 数据库配置
DB_CONFIG = {
    'host': '10.5.80.8',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': '2ketang',
    'charset': 'utf8mb4'
}


def execute_sql_file(filepath):
    """执行SQL文件"""
    print(f"正在读取SQL文件: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print("正在连接数据库...")
    connection = pymysql.connect(**DB_CONFIG)

    try:
        with connection.cursor() as cursor:
            # 分割SQL语句（按分号和DELIMITER）
            statements = []
            current_statement = []
            delimiter = ';'
            in_delimiter_block = False

            for line in sql_content.split('\n'):
                line = line.strip()

                # 跳过注释
                if line.startswith('--') or not line:
                    continue

                # 处理DELIMITER命令
                if line.startswith('DELIMITER'):
                    if '$$' in line:
                        delimiter = '$$'
                        in_delimiter_block = True
                    else:
                        delimiter = ';'
                        in_delimiter_block = False
                    continue

                current_statement.append(line)

                # 检查是否到达语句结尾
                if line.endswith(delimiter):
                    statement = ' '.join(current_statement)
                    statement = statement.rstrip(delimiter).strip()
                    if statement:
                        statements.append(statement)
                    current_statement = []

            # 执行所有语句
            print(f"\n开始执行SQL语句...")
            for i, statement in enumerate(statements, 1):
                try:
                    # 显示正在执行的语句（简短版本）
                    preview = statement[:100] + '...' if len(statement) > 100 else statement
                    print(f"\n[{i}/{len(statements)}] 执行: {preview}")

                    cursor.execute(statement)
                    connection.commit()

                    # 如果是SELECT语句，显示结果
                    if statement.upper().startswith('SELECT'):
                        results = cursor.fetchall()
                        if results:
                            for row in results:
                                print(f"  结果: {row}")

                    print(f"  [OK] 成功")

                except Exception as e:
                    print(f"  [FAIL] 失败: {e}")
                    # 某些错误可以忽略（如表已存在）
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"  (忽略此错误)")
                        continue
                    else:
                        raise

            print(f"\n{'='*60}")
            print("数据库初始化完成！")
            print(f"{'='*60}")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        connection.close()


if __name__ == "__main__":
    sql_file = "database_schema.sql"
    execute_sql_file(sql_file)
