#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫服务封装
提供高层次的爬虫接口
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.crawler_log import CrawlerTaskStatus
from app.crawlers.login import login
from app.crawlers.activity_crawler import crawl_all_tabs  # selenium 版,保留作 fallback
from app.crawlers import activity_api
from app.crawlers.detail_crawler import crawl_activity_detail, crawl_activity_details
from app.crawlers.participant_crawler import crawl_activity_participants, crawl_participants_batch
from app.crawlers.student_crawler import crawl_students
from app.services.crawler_task_manager import task_manager
from app.repositories import activity_repo, participant_repo, student_repo


class CrawlerService:
    """爬虫服务"""

    def __init__(self, db: Session, task_id: Optional[str] = None):
        """
        初始化爬虫服务

        Args:
            db: 数据库会话
            task_id: 任务ID（用于日志记录）
        """
        self.db = db
        self.driver = None
        self.task_id = task_id

    def start_driver(self) -> bool:
        """
        启动浏览器驱动

        Returns:
            是否成功
        """
        self._log("启动浏览器并登录...")
        self.driver = login()
        if self.driver:
            self._log("登录成功")
            return True
        else:
            self._log("登录失败")
            return False

    def stop_driver(self):
        """停止浏览器驱动"""
        if self.driver:
            self._log("关闭浏览器...")
            self.driver.quit()
            self.driver = None

    def crawl_activities(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        爬取所有标签页的活动

        Returns:
            活动字典，键为标签页名称
        """
        if not self.driver:
            if not self.start_driver():
                return {}

        self._log("开始爬取活动列表...")
        self._update_status(CrawlerTaskStatus.running)

        # 传递停止检查回调
        def stop_check():
            if self.task_id:
                return task_manager.should_stop(self.task_id)
            return False

        # 活动列表走源站 API(秒级,替代 selenium 翻页)
        activities = activity_api.crawl_all_activities_api(self.driver, stop_check=stop_check)

        # 检查停止信号
        if self._check_stop():
            return activities

        # 保存到数据库
        self._save_activities_to_db(activities)

        total_count = sum(len(v) for v in activities.values())
        self._log(f"活动列表爬取完成，共 {total_count} 个活动")

        return activities

    def crawl_activity_details_batch(
        self,
        act_ids: List[int],
        batch_size: int = 200,
    ) -> int:
        """
        批量爬取活动详情(API),分批入库(每 batch_size 个 commit 一次)。
        中途停止/异常时,已入库的批次保留,不会全丢。

        Args:
            act_ids: 活动ID列表
            batch_size: 每多少个详情入库一次

        Returns:
            成功保存的详情数
        """
        if not self.driver:
            if not self.start_driver():
                return 0

        total = len(act_ids)
        self._log(f"开始爬取 {total} 个活动的详情(分批入库,每 {batch_size} 个)...")
        self._update_status(CrawlerTaskStatus.running)
        self._update_progress(0, total)

        saved = 0
        batch: List[Dict[str, Any]] = []

        for i, aid in enumerate(act_ids, 1):
            if self._check_stop():
                break
            try:
                d = activity_api.fetch_activity_detail(self.driver, aid)
                if d:
                    batch.append(d)
            except Exception as e:
                self._log(f"详情 {aid} 拉取失败: {e}")

            if len(batch) >= batch_size:
                saved += activity_repo.save_details(self.db, batch)
                batch = []
                self._log(f"已保存 {saved}/{total} 个详情")
                self._update_progress(i, total)

        # 收尾剩余批次
        if batch:
            saved += activity_repo.save_details(self.db, batch)

        self._log(f"活动详情爬取完成，共保存 {saved} 个")
        self._update_progress(total, total)
        return saved

    def crawl_all_activity_details(self, statuses: Optional[List[str]] = None) -> int:
        """全量同步活动详情(API,分批入库)。

        statuses: 只爬这些状态的活动;None 则爬库里全部活动。
        从 activities 表取 act_id,逐个 detailById 拉完整详情(含 QQ 群)入库。
        返回成功保存的详情数。
        """
        from app.models import Activity
        q = self.db.query(Activity.act_id)
        if statuses:
            q = q.filter(Activity.finish_status.in_(statuses))
        act_ids = [r[0] for r in q.all() if r[0]]
        scope = "/".join(statuses) if statuses else "全部"
        self._log(f"全量详情同步({scope}): 共 {len(act_ids)} 个活动")
        if not act_ids:
            return 0
        return self.crawl_activity_details_batch(act_ids)

    def crawl_participants_for_activities(
        self,
        act_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        批量爬取活动参与者信息

        Args:
            act_ids: 活动ID列表

        Returns:
            参与者信息列表
        """
        if not self.driver:
            if not self.start_driver():
                return []

        self._log(f"开始爬取 {len(act_ids)} 个活动的参与者信息...")
        self._update_status(CrawlerTaskStatus.running)
        self._update_progress(0, len(act_ids))

        # 传递停止检查和进度回调
        def stop_check():
            if self.task_id:
                return task_manager.should_stop(self.task_id)
            return False
        
        def progress_callback(current, total):
            self._update_progress(current, total)

        results = crawl_participants_batch(self.driver, act_ids, stop_check=stop_check, progress_callback=progress_callback)

        # 检查停止信号
        if self._check_stop():
            return results

        # 保存到数据库
        self._save_participants_to_db(results)

        total_participants = sum(len(r.get("participants", [])) for r in results)
        self._log(f"参与者信息爬取完成，共 {total_participants} 条")
        self._update_progress(len(results), len(act_ids))

        return results

    def full_crawl(self, active_statuses: List[str] = None) -> Dict[str, Any]:
        """
        综合爬取: 一次登录跑完整流程
          1. 爬活动列表(全部状态 tab)
          2. 对 active_statuses 的活动爬详情(含 QQ 群)
          3. 对 active_statuses 的活动爬参与者

        Args:
            active_statuses: 第 2、3 步处理哪些状态的活动,默认 待开始 + 进行中

        Returns:
            汇总统计
        """
        if active_statuses is None:
            active_statuses = ["待开始", "进行中"]
        active_set = set(active_statuses)

        if not self.driver:
            if not self.start_driver():
                return {}

        def stop_check():
            return bool(self.task_id) and task_manager.should_stop(self.task_id)

        # ---------- 1. 活动列表 ----------
        self._log("【1/3】爬取活动列表(全部状态, API 提速)...")
        self._update_status(CrawlerTaskStatus.running)
        grouped = activity_api.crawl_all_activities_api(self.driver, stop_check=stop_check)
        if self._check_stop():
            return {}
        self._save_activities_to_db(grouped)
        total_acts = sum(len(v) for v in grouped.values())
        self._log(f"活动列表完成,共 {total_acts} 个")

        # 收集目标状态的活动 ID
        active_ids = []
        for status, acts in grouped.items():
            if status in active_set:
                for a in acts:
                    aid = a.get("actId") or a.get("act_id")
                    if aid:
                        active_ids.append(aid)
        active_ids = list(dict.fromkeys(active_ids))
        self._log(f"目标活动({'/'.join(active_statuses)}): {len(active_ids)} 个")

        details_count = 0
        participants_count = 0

        if active_ids and not self._check_stop():
            # ---------- 2. 活动详情 ----------
            self._log(f"【2/3】爬取 {len(active_ids)} 个活动详情(含 QQ 群)...")
            details_count = self.crawl_activity_details_batch(active_ids)

        if active_ids and not self._check_stop():
            # ---------- 3. 参与者 ----------
            self._log(f"【3/3】爬取 {len(active_ids)} 个活动的参与者...")
            results = self.crawl_participants_for_activities(active_ids)
            participants_count = sum(len(r.get("participants", [])) for r in results)

        summary = {
            "activities": total_acts,
            "active_ids": len(active_ids),
            "details": details_count,
            "participants": participants_count,
        }
        self._log(
            f"综合爬取完成: 活动 {total_acts} | 目标 {len(active_ids)} | "
            f"详情 {details_count} | 参与者 {participants_count} 人次"
        )
        return summary

    def crawl_students(self) -> List[Dict[str, Any]]:
        """
        爬取学生信息

        Returns:
            学生信息列表
        """
        if not self.driver:
            if not self.start_driver():
                return []

        self._log("开始爬取学生信息...")
        self._update_status(CrawlerTaskStatus.running)

        # 定义进度回调
        def progress_callback(current, total):
            self._update_progress(current, total)
            self._log(f"进度: {current}/{total}")

        # 定义停止检查回调
        def should_stop_callback():
            return self._check_stop()

        students = crawl_students(
            self.driver,
            progress_callback=progress_callback,
            should_stop_callback=should_stop_callback
        )

        # 检查停止信号
        if self._check_stop():
            return students

        # 保存到数据库
        self._save_students_to_db(students)

        self._log(f"学生信息爬取完成，共 {len(students)} 条")

        return students

    def _save_activities_to_db(self, activities_dict: Dict[str, List[Dict[str, Any]]]):
        """保存活动到数据库(委托 activity_repo)"""
        if self._check_stop():
            return
        self._log("保存活动到数据库...")
        n = activity_repo.save_activities(self.db, activities_dict)
        self._log(f"成功保存 {n} 个活动")

    def _save_activity_details_to_db(self, details: List[Dict[str, Any]]):
        """保存活动详情到数据库(委托 activity_repo)"""
        if self._check_stop():
            return
        self._log("保存活动详情到数据库...")
        n = activity_repo.save_details(self.db, details)
        self._log(f"成功保存 {n} 个活动详情")

    def _save_participants_to_db(self, results: List[Dict[str, Any]]):
        """保存参与者到数据库(委托 participant_repo)"""
        if self._check_stop():
            return
        self._log("保存参与者到数据库...")
        n = participant_repo.save_participants(self.db, results)
        self._log(f"成功保存 {n} 条参与者记录")

    def _save_students_to_db(self, students: List[Dict[str, Any]]):
        """保存学生到数据库(委托 student_repo)"""
        self._log("保存学生到数据库...")

        def on_progress(saved, total):
            self._log(f"已保存 {saved}/{total} 条学生记录")

        n = student_repo.save_students(
            self.db, students,
            should_stop=self._check_stop,
            on_progress=on_progress,
        )
        self._log(f"成功保存 {n} 条学生记录")

    def _log(self, message: str):
        """
        记录日志

        Args:
            message: 日志消息
        """
        if self.task_id:
            task_manager.append_log(self.task_id, self.db, message)
        else:
            print(message)

    def _check_stop(self) -> bool:
        """
        检查是否应该停止

        Returns:
            是否应该停止
        """
        if self.task_id and task_manager.should_stop(self.task_id):
            self._log("任务已停止")
            self._update_status(CrawlerTaskStatus.stopped)
            return True
        return False

    def _update_status(self, status: CrawlerTaskStatus):
        """
        更新任务状态

        Args:
            status: 任务状态
        """
        if self.task_id:
            task_manager.update_status(self.task_id, self.db, status)

    def _update_progress(self, current: int, total: int):
        """
        更新任务进度

        Args:
            current: 当前进度
            total: 总数
        """
        if self.task_id:
            task_manager.update_progress(self.task_id, self.db, current, total)


if __name__ == "__main__":
    # 测试代码
    from app.database import SessionLocal

    db = SessionLocal()
    crawler_service = CrawlerService(db)

    try:
        # 测试爬取活动
        activities = crawler_service.crawl_activities()
        print(f"\n爬取结果:")
        for tab_name, act_list in activities.items():
            print(f"  {tab_name}: {len(act_list)} 个活动")

    finally:
        crawler_service.stop_driver()
        db.close()
