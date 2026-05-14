#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二课堂爬虫主控脚本
按照需求文档流程执行完整的爬虫任务
"""
import sys
import time
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

# 添加项目路径
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.config import settings
from app.crawlers.login import login
from app.crawlers.activity_crawler import crawl_all_tabs
from app.crawlers.detail_crawler import crawl_activity_detail
from app.crawlers.participant_crawler import crawl_activity_participants
from app.services.notification_service import NotificationService
from app.services.crawler_service import CrawlerService
from app.models import Activity, ActivityDetail, ActivityParticipant


class MainCrawler:
    """主控爬虫"""

    def __init__(self, db: Session, test_mode: bool = True):
        """
        初始化主控爬虫

        Args:
            db: 数据库会话
            test_mode: 测试模式（不实际发送邮件）
        """
        self.db = db
        self.driver = None
        self.test_mode = test_mode
        self.notification_service = NotificationService(db, test_mode=test_mode)
        self.crawler_service = CrawlerService(db)

    def start(self):
        """启动浏览器并登录"""
        print("\n" + "=" * 60)
        print("第二课堂爬虫系统")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试模式: {'是' if self.test_mode else '否'}")
        print("=" * 60 + "\n")

        print("[1] 启动浏览器并登录...")
        self.driver = login()
        if not self.driver:
            print("    登录失败，无法继续")
            return False

        self.crawler_service.driver = self.driver
        print("    登录成功！\n")
        return True

    def stop(self):
        """关闭浏览器"""
        if self.driver:
            print("\n[*] 关闭浏览器...")
            time.sleep(2)
            self.driver.quit()
            self.driver = None

    def step1_crawl_activities(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        步骤1: 爬取活动列表（待审核、报名中、进行中）

        Returns:
            活动字典
        """
        print("\n" + "=" * 60)
        print("[步骤1] 爬取活动列表")
        print("=" * 60)

        activities = crawl_all_tabs(self.driver)

        # 保存到数据库
        self.crawler_service._save_activities_to_db(activities)

        total = sum(len(v) for v in activities.values())
        print(f"\n活动列表爬取完成，共 {total} 个活动")
        print(f"  - 待审核: {len(activities.get('待审核', []))} 个")
        print(f"  - 报名中: {len(activities.get('报名中', []))} 个")
        print(f"  - 进行中: {len(activities.get('进行中', []))} 个")

        return activities

    def step2_process_enrolling_activities(
        self,
        enrolling_activities: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        步骤2: 处理"报名中"的活动
        - 爬取活动详情
        - 提取QQ群
        - 匹配学生并发送通知

        Args:
            enrolling_activities: 报名中的活动列表

        Returns:
            处理统计
        """
        print("\n" + "=" * 60)
        print("[步骤2] 处理报名中的活动")
        print("=" * 60)

        total_count = len(enrolling_activities)
        processed_count = 0
        notified_count = 0
        skipped_count = 0

        for i, activity in enumerate(enrolling_activities, 1):
            act_id = activity.get("actId")
            act_name = activity.get("name", "未知活动")

            print(f"\n[{i}/{total_count}] 处理活动: {act_name} (ID: {act_id})")

            # 爬取活动详情
            print("    爬取活动详情...")
            detail = crawl_activity_detail(self.driver, act_id)

            if not detail:
                print(f"    爬取详情失败，跳过")
                skipped_count += 1
                continue

            # 保存详情到数据库
            self.crawler_service._save_activity_details_to_db([detail])

            # 检查是否有"后台导入"
            if detail.get("is_backend_import"):
                print(f"    检测到'后台导入'，跳过通知")
                skipped_count += 1
                processed_count += 1
                continue

            # 准备活动数据（用于通知）
            activity_data = self._prepare_activity_data(detail)

            # 发送新活动通知
            print("    发送新活动通知...")
            result = self.notification_service.send_new_activity_notification(activity_data)

            if result["status"] == "sent":
                notified_count += 1
                print(f"    [OK] 通知已发送给 {result['recipient_count']} 名学生")
            elif result["status"] == "skipped":
                skipped_count += 1
                print(f"    跳过通知: {result['reason']}")

            processed_count += 1

            # 延迟
            if i < total_count:
                time.sleep(settings.CRAWL_DELAY)

        print(f"\n报名中活动处理完成:")
        print(f"  - 总计: {total_count} 个")
        print(f"  - 已处理: {processed_count} 个")
        print(f"  - 已通知: {notified_count} 个")
        print(f"  - 已跳过: {skipped_count} 个")

        return {
            "total": total_count,
            "processed": processed_count,
            "notified": notified_count,
            "skipped": skipped_count
        }

    def step3_process_ongoing_activities(
        self,
        ongoing_activities: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        步骤3: 处理"进行中"的活动
        - 爬取活动详情
        - 爬取参与者信息
        - 检测签到/签退状态并发送通知

        Args:
            ongoing_activities: 进行中的活动列表

        Returns:
            处理统计
        """
        print("\n" + "=" * 60)
        print("[步骤3] 处理进行中的活动")
        print("=" * 60)

        total_count = len(ongoing_activities)
        processed_count = 0
        sign_in_notified = 0
        sign_out_notified = 0

        for i, activity in enumerate(ongoing_activities, 1):
            act_id = activity.get("actId")
            act_name = activity.get("name", "未知活动")

            print(f"\n[{i}/{total_count}] 处理活动: {act_name} (ID: {act_id})")

            # 爬取活动详情（获取完整信息）
            print("    爬取活动详情...")
            detail = crawl_activity_detail(self.driver, act_id)

            if not detail:
                print(f"    爬取详情失败，跳过")
                continue

            # 保存详情到数据库
            self.crawler_service._save_activity_details_to_db([detail])

            # 爬取参与者信息
            print("    爬取参与者信息...")
            result = crawl_activity_participants(self.driver, act_id)

            if not result:
                print(f"    爬取参与者信息失败，跳过")
                continue

            participants = result.get("participants", [])
            status = result.get("status", {})

            # 保存参与者到数据库
            self.crawler_service._save_participants_to_db([result])

            # 准备活动数据（用于通知）
            activity_data = self._prepare_activity_data(detail)

            # 检查签到状态并发送通知
            if status.get("has_sign_in"):
                print("    检测到签到记录，发送签到提醒...")
                sign_in_result = self.notification_service.send_sign_in_notification(
                    activity_data, participants
                )
                if sign_in_result["status"] == "sent":
                    sign_in_notified += 1
                    print(f"    [OK] 签到提醒已发送给 {sign_in_result['recipient_count']} 名学生")
                else:
                    print(f"    签到提醒跳过: {sign_in_result.get('reason', '未知')}")

            # 检查签退状态并发送通知
            if status.get("has_sign_out"):
                print("    检测到签退记录，发送签退提醒...")
                sign_out_result = self.notification_service.send_sign_out_notification(
                    activity_data, participants
                )
                if sign_out_result["status"] == "sent":
                    sign_out_notified += 1
                    print(f"    [OK] 签退提醒已发送给 {sign_out_result['recipient_count']} 名学生")
                else:
                    print(f"    签退提醒跳过: {sign_out_result.get('reason', '未知')}")

            processed_count += 1

            # 延迟
            if i < total_count:
                time.sleep(settings.CRAWL_DELAY)

        print(f"\n进行中活动处理完成:")
        print(f"  - 总计: {total_count} 个")
        print(f"  - 已处理: {processed_count} 个")
        print(f"  - 签到提醒: {sign_in_notified} 个")
        print(f"  - 签退提醒: {sign_out_notified} 个")

        return {
            "total": total_count,
            "processed": processed_count,
            "sign_in_notified": sign_in_notified,
            "sign_out_notified": sign_out_notified
        }

    def _prepare_activity_data(self, detail: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备活动数据（用于通知）

        Args:
            detail: 活动详情

        Returns:
            活动数据字典
        """
        return {
            "act_id": detail.get("actId"),
            "act_name": detail.get("actName"),
            "class_name": detail.get("calssName"),  # 注意原数据拼写
            "org_name": detail.get("orgName"),
            "start_time": self.crawler_service._timestamp_to_datetime(detail.get("starTime")),
            "end_time": self.crawler_service._timestamp_to_datetime(detail.get("endTime")),
            "enroll_end_time": self.crawler_service._timestamp_to_datetime(detail.get("enrollEndTime")),
            "pitch_address": detail.get("pitchAddress"),
            "job": detail.get("job"),
            "introduce": detail.get("introduce"),
            "qq_groups": detail.get("qq_groups"),
            "people_limit": detail.get("peopleLimit"),
            "college_name": detail.get("collegeName"),
            "grade_name": detail.get("gradeName"),
            "is_backend_import": detail.get("is_backend_import", False)
        }

    def run(self):
        """运行完整的爬虫流程"""
        start_time = datetime.now()

        try:
            # 启动浏览器并登录
            if not self.start():
                return

            # 步骤1: 爬取活动列表
            activities = self.step1_crawl_activities()

            # 步骤2: 处理报名中的活动
            enrolling_activities = activities.get("报名中", [])
            if enrolling_activities:
                self.step2_process_enrolling_activities(enrolling_activities)
            else:
                print("\n没有报名中的活动，跳过步骤2")

            # 步骤3: 处理进行中的活动
            ongoing_activities = activities.get("进行中", [])
            if ongoing_activities:
                self.step3_process_ongoing_activities(ongoing_activities)
            else:
                print("\n没有进行中的活动，跳过步骤3")

        except KeyboardInterrupt:
            print("\n\n用户中断...")
        except Exception as e:
            print(f"\n\n爬虫异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 关闭浏览器
            self.stop()

            # 统计
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print("\n" + "=" * 60)
            print("爬虫任务完成")
            print("=" * 60)
            print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"耗时: {duration:.2f} 秒")
            print("=" * 60 + "\n")


def main():
    """主函数"""
    db = SessionLocal()

    try:
        # 创建主控爬虫
        crawler = MainCrawler(db, test_mode=settings.TEST_MODE)

        # 运行
        crawler.run()

    finally:
        db.close()


if __name__ == "__main__":
    main()
