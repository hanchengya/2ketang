#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块测试脚本
"""
import sys
import traceback


def test_qq_extractor():
    """测试QQ群提取工具"""
    print("\n" + "="*60)
    print("测试 QQ群提取工具")
    print("="*60)

    try:
        from app.utils.qq_extractor import extract_qq_groups, format_qq_groups

        test_cases = [
            "请加入QQ群：123456789，或者联系987654321",
            "活动QQ群: 111222333, 444555666",
            "没有QQ群",
            "电话：13800138000，QQ群：12345678"
        ]

        for i, text in enumerate(test_cases, 1):
            groups = extract_qq_groups(text)
            formatted = format_qq_groups(groups)
            print(f"\n测试 {i}:")
            print(f"  输入: {text}")
            print(f"  提取: {groups}")
            print(f"  格式化: {formatted}")

        print("\n[OK] QQ群提取工具测试通过")
        return True

    except Exception as e:
        print(f"\n[FAIL] QQ群提取工具测试失败: {e}")
        traceback.print_exc()
        return False


def test_email_template():
    """测试邮件模板"""
    print("\n" + "="*60)
    print("测试 邮件模板")
    print("="*60)

    try:
        from app.utils.email_template import (
            render_new_activity_email,
            render_sign_in_email,
            render_sign_out_email
        )
        from datetime import datetime

        test_activity = {
            "act_id": 1,
            "act_name": "测试活动",
            "class_name": "测试分类",
            "org_name": "测试主办方",
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "pitch_address": "测试地点",
            "job": 0,
            "introduce": "这是一个测试活动，QQ群：123456789",
            "qq_groups": "123456789",
            "people_limit": 100,
            "enroll_end_time": datetime.now(),
            "college_name": "不限",
            "grade_name": "不限"
        }

        # 测试新活动邮件模板
        html1 = render_new_activity_email(test_activity)
        print(f"\n新活动邮件模板长度: {len(html1)} 字符")
        print(f"包含活动名称: {'测试活动' in html1}")

        # 测试签到邮件模板
        html2 = render_sign_in_email(test_activity)
        print(f"\n签到邮件模板长度: {len(html2)} 字符")
        print(f"包含活动名称: {'测试活动' in html2}")

        # 测试签退邮件模板
        html3 = render_sign_out_email(test_activity)
        print(f"\n签退邮件模板长度: {len(html3)} 字符")
        print(f"包含活动名称: {'测试活动' in html3}")

        print("\n[OK] 邮件模板测试通过")
        return True

    except Exception as e:
        print(f"\n[FAIL] 邮件模板测试失败: {e}")
        traceback.print_exc()
        return False


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "="*60)
    print("测试 数据库连接")
    print("="*60)

    try:
        import pymysql
        from app.config import settings

        print(f"\n数据库配置:")
        print(f"  Host: {settings.DB_HOST}")
        print(f"  Port: {settings.DB_PORT}")
        print(f"  Database: {settings.DB_NAME}")
        print(f"  User: {settings.DB_USER}")

        # 测试连接
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset=settings.DB_CHARSET
        )

        with connection.cursor() as cursor:
            # 测试查询
            cursor.execute("SELECT COUNT(*) FROM students WHERE email IS NOT NULL")
            count = cursor.fetchone()[0]
            print(f"\n有邮箱的学生数: {count}")

            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            print(f"管理员用户数: {count}")

            cursor.execute("SELECT COUNT(*) FROM activity_notifications")
            count = cursor.fetchone()[0]
            print(f"通知记录数: {count}")

        connection.close()

        print("\n[OK] 数据库连接测试通过")
        return True

    except Exception as e:
        print(f"\n[FAIL] 数据库连接测试失败: {e}")
        traceback.print_exc()
        return False


def test_models():
    """测试数据模型"""
    print("\n" + "="*60)
    print("测试 数据模型")
    print("="*60)

    try:
        from app.models import (
            Student, Activity, ActivityDetail,
            ActivityNotification, ActivityParticipant, EmailLog,
            User, NotificationType, EmailStatus, UserRole
        )

        print("\n导入的模型:")
        models = [
            Student, Activity, ActivityDetail,
            ActivityNotification, ActivityParticipant, EmailLog, User
        ]
        for model in models:
            print(f"  - {model.__name__}")

        print("\n枚举类型:")
        print(f"  - NotificationType: {[t.value for t in NotificationType]}")
        print(f"  - EmailStatus: {[s.value for s in EmailStatus]}")
        print(f"  - UserRole: {[r.value for r in UserRole]}")

        print("\n[OK] 数据模型测试通过")
        return True

    except Exception as e:
        print(f"\n[FAIL] 数据模型测试失败: {e}")
        traceback.print_exc()
        return False


def test_config():
    """测试配置"""
    print("\n" + "="*60)
    print("测试 配置")
    print("="*60)

    try:
        from app.config import settings

        print(f"\n应用配置:")
        print(f"  应用名称: {settings.APP_NAME}")
        print(f"  版本: {settings.APP_VERSION}")
        print(f"  调试模式: {settings.DEBUG}")
        print(f"  测试模式: {settings.TEST_MODE}")

        print(f"\n邮箱配置:")
        print(f"  SMTP服务器: {settings.SMTP_SERVER}")
        print(f"  SMTP端口: {settings.SMTP_PORT}")
        print(f"  发件人: {settings.SENDER_EMAIL}")
        print(f"  发件人名称: {settings.SENDER_NAME}")

        print(f"\n第二课堂配置:")
        print(f"  用户名: {settings.KETANG_USERNAME}")
        print(f"  登录URL: {settings.KETANG_LOGIN_URL}")

        print("\n[OK] 配置测试通过")
        return True

    except Exception as e:
        print(f"\n[FAIL] 配置测试失败: {e}")
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("第二课堂活动通知系统 - 模块测试")
    print("="*60)

    tests = [
        ("配置", test_config),
        ("QQ群提取工具", test_qq_extractor),
        ("邮件模板", test_email_template),
        ("数据模型", test_models),
        ("数据库连接", test_database_connection),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] 测试 {name} 时发生异常: {e}")
            traceback.print_exc()
            results.append((name, False))

    # 显示测试结果汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    passed = 0
    failed = 0
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")

    if failed == 0:
        print("\n所有测试通过！")
        return 0
    else:
        print(f"\n有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
