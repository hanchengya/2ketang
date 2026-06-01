#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫服务封装
提供高层次的爬虫接口
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert
from datetime import datetime

from app.models import Activity, ActivityDetail, ActivityParticipant, Student
from app.models.crawler_log import CrawlerTaskStatus
from app.crawlers.login import login
from app.crawlers.activity_crawler import crawl_all_tabs
from app.crawlers.detail_crawler import crawl_activity_detail, crawl_activity_details
from app.crawlers.participant_crawler import crawl_activity_participants, crawl_participants_batch
from app.crawlers.student_crawler import crawl_students
from app.services.crawler_task_manager import task_manager


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

        activities = crawl_all_tabs(self.driver, stop_check=stop_check)

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
        act_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        批量爬取活动详情

        Args:
            act_ids: 活动ID列表

        Returns:
            活动详情列表
        """
        if not self.driver:
            if not self.start_driver():
                return []

        self._log(f"开始爬取 {len(act_ids)} 个活动的详情...")
        self._update_status(CrawlerTaskStatus.running)
        self._update_progress(0, len(act_ids))

        # 传递停止检查和进度回调
        def stop_check():
            if self.task_id:
                return task_manager.should_stop(self.task_id)
            return False
        
        def progress_callback(current, total):
            self._update_progress(current, total)

        details = crawl_activity_details(self.driver, act_ids, stop_check=stop_check, progress_callback=progress_callback)

        # 检查停止信号
        if self._check_stop():
            return details

        # 保存到数据库
        self._save_activity_details_to_db(details)

        self._log(f"活动详情爬取完成，共 {len(details)} 个")
        self._update_progress(len(details), len(act_ids))

        return details

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
        self._log("【1/3】爬取活动列表(全部状态)...")
        self._update_status(CrawlerTaskStatus.running)
        grouped = crawl_all_tabs(self.driver, stop_check=stop_check)
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
            details = self.crawl_activity_details_batch(active_ids)
            details_count = len(details)

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
        """保存活动到数据库"""
        self._log("保存活动到数据库...")
        total_saved = 0

        for tab_name, activities in activities_dict.items():
            # 根据标签页名称确定活动状态
            tab_status = tab_name  # 标签页名称就是状态：待审核、报名中、进行中
            
            for activity in activities:
                # 检查停止信号
                if self._check_stop():
                    return

                try:
                    # 使用标签页名称作为状态，如果API返回了finishStatus则优先使用
                    activity_status = activity.get("finishStatus") or tab_status
                    
                    # 检查是否已存在
                    existing = self.db.query(Activity).filter(
                        Activity.act_id == activity.get("actId")
                    ).first()

                    if existing:
                        # 更新关键字段
                        existing.start_time = self._timestamp_to_datetime(activity.get("startTime"))
                        existing.end_time = self._timestamp_to_datetime(activity.get("endTime"))
                        existing.enroll_end_time = self._timestamp_to_datetime(activity.get("enrollEndTime"))
                        existing.finish_status = activity_status
                        existing.finish_status2 = activity.get("finishStatus2", "")
                    else:
                        # 新建
                        new_activity = Activity(
                            act_id=activity.get("actId"),
                            name=activity.get("name"),
                            class_id=activity.get("classId"),
                            class_name=activity.get("className"),
                            org_id=activity.get("orgId"),
                            org_name=activity.get("orgName"),
                            admin_id=activity.get("adminId"),
                            admin_code=activity.get("adminCode"),
                            admin_name=activity.get("adminName"),
                            creator_id=activity.get("creatorId"),
                            hours=activity.get("hours"),
                            start_time=self._timestamp_to_datetime(activity.get("startTime")),
                            end_time=self._timestamp_to_datetime(activity.get("endTime")),
                            enroll_end_time=self._timestamp_to_datetime(activity.get("enrollEndTime")),
                            status=activity.get("status"),
                            apply_status=activity.get("applyStatus"),
                            status_all=activity.get("statusAll"),
                            oto=activity.get("oto"),
                            edit_activity=activity.get("editActivity"),
                            chenge_status=activity.get("chengeStatus"),
                            finish_status=activity_status,
                            finish_status2=activity.get("finishStatus2")
                        )
                        self.db.add(new_activity)

                    total_saved += 1

                except Exception as e:
                    self._log(f"保存活动 {activity.get('actId')} 失败: {e}")

        self.db.commit()
        self._log(f"成功保存 {total_saved} 个活动")

    def _save_activity_details_to_db(self, details: List[Dict[str, Any]]):
        """保存活动详情到数据库"""
        self._log("保存活动详情到数据库...")
        total_saved = 0

        for detail in details:
            # 检查停止信号
            if self._check_stop():
                return

            try:
                # 检查是否已存在
                existing = self.db.query(ActivityDetail).filter(
                    ActivityDetail.act_id == detail.get("actId")
                ).first()

                if existing:
                    # 更新关键字段
                    existing.introduce = detail.get("introduce")
                    existing.college_name = detail.get("collegeName")
                    existing.grade_name = detail.get("gradeName")
                    existing.qq_groups = detail.get("qq_groups")
                else:
                    # 新建（简化版，只保存关键字段）
                    new_detail = ActivityDetail(
                        act_id=detail.get("actId"),
                        act_name=detail.get("actName"),
                        introduce=detail.get("introduce"),
                        org_id=detail.get("orgId"),
                        org_name=detail.get("orgName"),
                        class_id=detail.get("classId"),
                        class_name=detail.get("calssName"),  # 注意原数据拼写
                        start_time=self._timestamp_to_datetime(detail.get("starTime")),
                        end_time=self._timestamp_to_datetime(detail.get("endTime")),
                        enroll_end_time=self._timestamp_to_datetime(detail.get("enrollEndTime")),
                        hours=detail.get("hours"),
                        people_limit=detail.get("peopleLimit"),
                        pitch_address=detail.get("pitchAddress"),
                        college_name=detail.get("collegeName"),
                        grade_name=detail.get("gradeName"),
                        job=detail.get("job"),
                        qq_groups=detail.get("qq_groups")
                    )
                    self.db.add(new_detail)

                total_saved += 1

            except Exception as e:
                self._log(f"保存活动详情 {detail.get('actId')} 失败: {e}")

        self.db.commit()
        self._log(f"成功保存 {total_saved} 个活动详情")

    def _save_participants_to_db(self, results: List[Dict[str, Any]]):
        """保存参与者到数据库"""
        self._log("保存参与者到数据库...")
        total_saved = 0

        for result in results:
            act_id = result.get("act_id")
            participants = result.get("participants", [])

            for participant in participants:
                # 检查停止信号
                if self._check_stop():
                    return

                try:
                    student_code = participant.get("code") or participant.get("studentCode") or participant.get("stuCode")
                    if not student_code:
                        continue

                    # 检查是否已存在
                    existing = self.db.query(ActivityParticipant).filter(
                        ActivityParticipant.act_id == act_id,
                        ActivityParticipant.student_code == student_code
                    ).first()

                    sign_in_time = self._timestamp_to_datetime(
                        participant.get("signInTime") or participant.get("sign_in_time") or participant.get("inTime")
                    )
                    sign_out_time = self._timestamp_to_datetime(
                        participant.get("signOutTime") or participant.get("sign_out_time") or participant.get("outTime")
                    )

                    if existing:
                        # 更新
                        existing.sign_in_time = sign_in_time
                        existing.sign_out_time = sign_out_time
                    else:
                        # 新建
                        new_participant = ActivityParticipant(
                            act_id=act_id,
                            student_code=student_code,
                            student_name=participant.get("name") or participant.get("studentName") or participant.get("stuName"),
                            sign_in_time=sign_in_time,
                            sign_out_time=sign_out_time,
                            credits=participant.get("credits")
                        )
                        self.db.add(new_participant)

                    total_saved += 1

                except Exception as e:
                    self._log(f"保存参与者失败: {e}")

        self.db.commit()
        self._log(f"成功保存 {total_saved} 条参与者记录")

    def _save_students_to_db(self, students: List[Dict[str, Any]]):
        """保存学生到数据库"""
        self._log("保存学生到数据库...")
        total_saved = 0
        batch_size = 500

        def clean_value(value):
            if value == "":
                return None
            return value

        def build_values(student: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            student_code = str(student.get("code") or "").strip()
            if not student_code:
                return None

            return {
                "code": student_code,
                "id": clean_value(student.get("id")),
                "name": clean_value(student.get("name")),
                "gender": clean_value(student.get("gender")),
                "ethnic": clean_value(student.get("ethnic")),
                "politics": clean_value(student.get("politics")),
                "mobile": clean_value(student.get("mobile")),
                "campus_id": clean_value(student.get("campusId")),
                "campus_name": clean_value(student.get("campusName")),
                "college_id": clean_value(student.get("collegeId")),
                "college_name": clean_value(student.get("collegeName")),
                "major_id": clean_value(student.get("majorId")),
                "major_name": clean_value(student.get("majorName")),
                "class_id": clean_value(student.get("classId")),
                "class_name": clean_value(student.get("className")),
                "grade": clean_value(student.get("grade")),
                "grade_name": clean_value(student.get("gradeName")),
                "length_name": clean_value(student.get("lengthName")),
                "credit": clean_value(student.get("credit")),
                "sum_score": clean_value(student.get("sumScore")),
                "user_class_pass": clean_value(student.get("userClassPass")),
                "status": clean_value(student.get("status")),
                "leave_total_num": clean_value(student.get("leaveTotalNum")),
                "leave_success_num": clean_value(student.get("leaveSuccessNum")),
                "leave_fail_num": clean_value(student.get("leaveFailNum"))
            }

        def save_batch(batch: List[Dict[str, Any]]) -> int:
            if not batch:
                return 0

            stmt = mysql_insert(Student).values(batch)
            update_values = {
                key: stmt.inserted[key]
                for key in batch[0].keys()
                if key != "code"
            }
            self.db.execute(stmt.on_duplicate_key_update(**update_values))
            return len(batch)

        batch = []

        for student in students:
            # 检查停止信号
            if self._check_stop():
                return

            try:
                values = build_values(student)
                if not values:
                    continue

                batch.append(values)
                if len(batch) >= batch_size:
                    total_saved += save_batch(batch)
                    self.db.commit()
                    batch = []

                    if total_saved % 5000 == 0:
                        self._log(f"已保存 {total_saved}/{len(students)} 条学生记录")

            except Exception as e:
                self.db.rollback()
                self._log(f"保存学生 {student.get('code')} 失败: {e}")
                batch = []

        if batch:
            total_saved += save_batch(batch)
        self.db.commit()
        self._log(f"成功保存 {total_saved} 条学生记录")

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """驼峰转下划线"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def _timestamp_to_datetime(ts) -> Optional[datetime]:
        """时间戳转datetime，支持数字时间戳和字符串格式

        如果有多个时间（逗号分隔），取第一个时间
        """
        if not ts:
            return None
        try:
            # 如果是字符串且包含逗号，取第一个时间
            if isinstance(ts, str) and ',' in ts:
                ts = ts.split(',')[0].strip()

            if isinstance(ts, (int, float)) and ts > 0:
                if ts > 10000000000:
                    ts = ts / 1000
                return datetime.fromtimestamp(ts)
            elif isinstance(ts, str):
                ts = ts.strip()
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                    try:
                        return datetime.strptime(ts, fmt)
                    except:
                        continue
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except:
            return None
        return None

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
