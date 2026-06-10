#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫控制API
"""
from typing import Any, List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User
from app.models.crawler_log import CrawlerTaskType, CrawlerTaskStatus
from app.services.crawler_service import CrawlerService
from app.services.crawler_task_manager import task_manager
from app.services.scheduler_service import scheduler

router = APIRouter()


# ============ 请求/响应模型 ============

class CrawlerStatusResponse(BaseModel):
    """爬虫状态响应"""
    status: str
    message: str


class CrawlActivitiesRequest(BaseModel):
    """爬取活动请求"""
    save_to_db: bool = True


class CrawlDetailsRequest(BaseModel):
    """爬取详情请求"""
    act_ids: List[int]
    save_to_db: bool = True


class CrawlParticipantsRequest(BaseModel):
    """爬取参与者请求"""
    act_ids: List[int]
    save_to_db: bool = True


class TaskStartResponse(BaseModel):
    """任务启动响应"""
    task_id: str
    status: str
    message: str


# ============ API端点 ============

@router.get("/status", response_model=CrawlerStatusResponse)
def get_crawler_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取爬虫状态

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        爬虫状态
    """
    running_tasks = task_manager.get_running_tasks(db)

    if running_tasks:
        return CrawlerStatusResponse(
            status="running",
            message=f"{len(running_tasks)} 个任务正在运行"
        )
    else:
        return CrawlerStatusResponse(
            status="idle",
            message="没有正在运行的任务"
        )


@router.post("/crawl-activities", response_model=TaskStartResponse)
def crawl_activities(
    request: CrawlActivitiesRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    启动爬取活动列表任务

    Args:
        request: 爬取请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户

    Returns:
        任务启动响应
    """
    # 创建任务
    task_id = task_manager.create_task(CrawlerTaskType.activities, db)

    def run_crawler():
        from app.database import SessionLocal
        db_session = SessionLocal()
        try:
            crawler_service = CrawlerService(db_session, task_id)
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.running, "开始爬取活动列表")

            activities = crawler_service.crawl_activities()

            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                total = sum(len(v) for v in activities.values())
                task_manager.update_status(
                    task_id, db_session, CrawlerTaskStatus.completed,
                    f"活动列表爬取完成，共 {total} 个活动"
                )
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"任务失败: {str(e)}")
        finally:
            crawler_service.stop_driver()
            db_session.close()

    # 添加到后台任务
    background_tasks.add_task(run_crawler)

    return TaskStartResponse(
        task_id=task_id,
        status="started",
        message="活动列表爬取任务已启动"
    )


@router.post("/crawl-details", response_model=TaskStartResponse)
def crawl_details(
    request: CrawlDetailsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    启动爬取活动详情任务

    Args:
        request: 爬取请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户

    Returns:
        任务启动响应
    """
    # 创建任务
    task_id = task_manager.create_task(CrawlerTaskType.details, db, total_count=len(request.act_ids))

    def run_crawler():
        from app.database import SessionLocal
        db_session = SessionLocal()
        try:
            crawler_service = CrawlerService(db_session, task_id)
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.running,
                                      f"开始爬取 {len(request.act_ids)} 个活动的详情")

            details = crawler_service.crawl_activity_details_batch(request.act_ids)

            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                task_manager.update_status(
                    task_id, db_session, CrawlerTaskStatus.completed,
                    f"活动详情爬取完成，共 {len(details)} 个"
                )
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"任务失败: {str(e)}")
        finally:
            crawler_service.stop_driver()
            db_session.close()

    # 添加到后台任务
    background_tasks.add_task(run_crawler)

    return TaskStartResponse(
        task_id=task_id,
        status="started",
        message=f"活动详情爬取任务已启动，共 {len(request.act_ids)} 个活动"
    )


@router.post("/crawl-students", response_model=TaskStartResponse)
def crawl_students(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    启动爬取学生信息任务

    Args:
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户

    Returns:
        任务启动响应
    """
    # 创建任务
    task_id = task_manager.create_task(CrawlerTaskType.students, db)

    def run_crawler():
        from app.database import SessionLocal
        db_session = SessionLocal()
        try:
            crawler_service = CrawlerService(db_session, task_id)
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.running, "开始爬取学生信息")

            students = crawler_service.crawl_students()

            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                task_manager.update_status(
                    task_id, db_session, CrawlerTaskStatus.completed,
                    f"学生信息爬取完成，共 {len(students)} 条"
                )
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"任务失败: {str(e)}")
        finally:
            crawler_service.stop_driver()
            db_session.close()

    # 添加到后台任务
    background_tasks.add_task(run_crawler)

    return TaskStartResponse(
        task_id=task_id,
        status="started",
        message="学生信息爬取任务已启动"
    )


@router.post("/crawl-participants", response_model=TaskStartResponse)
def crawl_participants(
    request: CrawlParticipantsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    启动爬取参与者信息任务

    Args:
        request: 爬取请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户

    Returns:
        任务启动响应
    """
    # 创建任务
    task_id = task_manager.create_task(CrawlerTaskType.participants, db, total_count=len(request.act_ids))

    def run_crawler():
        from app.database import SessionLocal
        db_session = SessionLocal()
        try:
            crawler_service = CrawlerService(db_session, task_id)
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.running,
                                      f"开始爬取 {len(request.act_ids)} 个活动的参与者信息")

            results = crawler_service.crawl_participants_for_activities(request.act_ids)

            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                total = sum(len(r.get("participants", [])) for r in results)
                task_manager.update_status(
                    task_id, db_session, CrawlerTaskStatus.completed,
                    f"参与者信息爬取完成，共 {total} 条"
                )
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"任务失败: {str(e)}")
        finally:
            crawler_service.stop_driver()
            db_session.close()

    # 添加到后台任务
    background_tasks.add_task(run_crawler)

    return TaskStartResponse(
        task_id=task_id,
        status="started",
        message=f"参与者信息爬取任务已启动，共 {len(request.act_ids)} 个活动"
    )


@router.post("/full-crawl", response_model=TaskStartResponse)
def full_crawl(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    一键综合爬取: 活动列表 → 待开始/进行中的详情(含 QQ 群) → 同批参与者。
    复用任务管理(日志/停止/进度)。
    """
    task_id = task_manager.create_task(CrawlerTaskType.full, db)

    def run_crawler():
        from app.database import SessionLocal
        db_session = SessionLocal()
        crawler_service = CrawlerService(db_session, task_id)
        try:
            task_manager.update_status(
                task_id, db_session, CrawlerTaskStatus.running,
                "开始综合爬取(列表+待开始/进行中的详情+参与者)"
            )

            summary = crawler_service.full_crawl(active_statuses=["待开始", "进行中"])

            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                task_manager.update_status(
                    task_id, db_session, CrawlerTaskStatus.completed,
                    f"综合爬取完成: 活动 {summary.get('activities', 0)} | "
                    f"详情 {summary.get('details', 0)} | "
                    f"参与者 {summary.get('participants', 0)} 人次"
                )
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"任务失败: {str(e)}")
        finally:
            crawler_service.stop_driver()
            db_session.close()

    background_tasks.add_task(run_crawler)

    return TaskStartResponse(
        task_id=task_id,
        status="started",
        message="综合爬取任务已启动"
    )


@router.post("/notify-sign", response_model=TaskStartResponse)
def notify_sign(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """手动触发: 检查进行中活动的签到/签退,达阈值给报名者发订阅消息(每活动每类型只发一次)。"""
    task_id = task_manager.create_task(CrawlerTaskType.script_sign_in, db)

    def run():
        from app.database import SessionLocal
        from app.crawlers.login import login
        from app.services.signin_notify_service import run_sign_notify
        db_session = SessionLocal()
        driver = None
        try:
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.running, "登录并检查签到/签退...")
            driver = login()
            if not driver:
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, "登录失败")
                return

            def stop_check():
                return task_manager.should_stop(task_id)

            summary = run_sign_notify(
                db_session, driver,
                stop_check=stop_check,
                log_fn=lambda m: task_manager.append_log(task_id, db_session, m),
            )
            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                task_manager.update_status(
                    task_id, db_session, CrawlerTaskStatus.completed,
                    f"完成: 签到通知 {summary['sign_in_sent']} / 签退通知 {summary['sign_out_sent']}, "
                    f"消息成功 {summary['msg_success']} 失败 {summary['msg_fail']}"
                )
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"任务失败: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            db_session.close()

    background_tasks.add_task(run)
    return TaskStartResponse(task_id=task_id, status="started", message="签到/签退通知任务已启动")


@router.post("/notify-enrolled", response_model=TaskStartResponse)
def notify_enrolled(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """手动触发: 给待开始活动的报名者发"报名成功"通知(每活动只发一次)。"""
    task_id = task_manager.create_task(CrawlerTaskType.script_new_activity, db)

    def run():
        from app.database import SessionLocal
        from app.crawlers.login import login
        from app.services.enrolled_notify_service import run_enrolled_notify
        db_session = SessionLocal()
        driver = None
        try:
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.running, "登录并检查待开始活动报名...")
            driver = login()
            if not driver:
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, "登录失败")
                return

            def stop_check():
                return task_manager.should_stop(task_id)

            summary = run_enrolled_notify(
                db_session, driver,
                stop_check=stop_check,
                log_fn=lambda m: task_manager.append_log(task_id, db_session, m),
            )
            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                task_manager.update_status(
                    task_id, db_session, CrawlerTaskStatus.completed,
                    f"完成: 报名成功通知 {summary['sent']} 活动, "
                    f"消息成功 {summary['msg_success']} 失败 {summary['msg_fail']}"
                )
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"任务失败: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            db_session.close()

    background_tasks.add_task(run)
    return TaskStartResponse(task_id=task_id, status="started", message="报名成功通知任务已启动")


@router.post("/notify-enrollable", response_model=TaskStartResponse)
def notify_enrollable(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """手动触发: 给报名中活动的有权限已绑定学生发"可报名"通知(每活动只发一次)。"""
    task_id = task_manager.create_task(CrawlerTaskType.script_new_activity, db)

    def run():
        from app.database import SessionLocal
        from app.crawlers.login import login
        from app.services.enrollable_notify_service import run_enrollable_notify
        db_session = SessionLocal()
        driver = None
        try:
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.running, "登录并检查报名中活动...")
            driver = login()
            if not driver:
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, "登录失败")
                return

            def stop_check():
                return task_manager.should_stop(task_id)

            summary = run_enrollable_notify(
                db_session, driver,
                stop_check=stop_check,
                log_fn=lambda m: task_manager.append_log(task_id, db_session, m),
            )
            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                task_manager.update_status(
                    task_id, db_session, CrawlerTaskStatus.completed,
                    f"完成: 可报名通知 {summary['sent']} 活动, "
                    f"消息成功 {summary['msg_success']} 失败 {summary['msg_fail']}"
                )
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"任务失败: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            db_session.close()

    background_tasks.add_task(run)
    return TaskStartResponse(task_id=task_id, status="started", message="可报名通知任务已启动")


@router.post("/stop/{task_id}")
def stop_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    停止指定任务

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        停止响应
    """
    task_info = task_manager.get_task_info(task_id, db)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task_info["status"] != "running":
        return {
            "status": "error",
            "message": f"任务当前状态为 {task_info['status']}，无法停止"
        }

    task_manager.request_stop(task_id, db)
    
    # 立即更新任务状态为停止，不等待爬虫响应
    task_manager.update_status(task_id, db, CrawlerTaskStatus.stopped, "用户请求停止任务")

    return {
        "status": "success",
        "message": "任务已停止"
    }


@router.get("/tasks")
def get_all_tasks(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取所有任务列表

    Args:
        skip: 跳过数量
        limit: 返回数量
        db: 数据库会话
        current_user: 当前用户

    Returns:
        任务列表
    """
    tasks = task_manager.get_all_tasks(db)

    # 分页
    total = len(tasks)
    tasks = tasks[skip:skip + limit]

    return {
        "total": total,
        "items": tasks
    }


@router.get("/tasks/{task_id}")
def get_task_info(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取任务详情

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        任务详情
    """
    task_info = task_manager.get_task_info(task_id, db)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task_info


@router.get("/logs/{task_id}")
def get_task_logs(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取任务日志

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        任务日志
    """
    task_info = task_manager.get_task_info(task_id, db)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "task_id": task_id,
        "log_content": task_info.get("log_content", "")
    }


@router.post("/test-email")
def test_email(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    测试邮件发送

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        测试结果
    """
    from app.services.email_service import EmailService
    from app.models import NotificationType
    from datetime import datetime

    email_service = EmailService(db, test_mode=True)

    test_activity = {
        "act_id": 9999,
        "act_name": "测试活动",
        "class_name": "测试分类",
        "org_name": "测试主办方",
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "pitch_address": "测试地点",
        "job": 0,
        "introduce": "这是一个测试活动",
        "qq_groups": "123456789",
        "people_limit": 100,
        "enroll_end_time": datetime.now(),
        "college_name": "不限",
        "grade_name": "不限"
    }

    result = email_service.send_email(
        to_email="test@example.com",
        subject="测试邮件",
        html_content="<h1>测试邮件内容</h1>",
        act_id=9999,
        student_code="TEST001",
        email_type=NotificationType.NEW_ACTIVITY
    )

    return {
        "status": "success" if result else "failed",
        "message": "Test email sent (test mode)" if result else "Test email failed"
    }


# ============ 定时任务API ============

class ScheduleRequest(BaseModel):
    """定时任务请求"""
    crawler_type: str  # activities, details, students
    interval_minutes: int = 60  # 间隔时间（分钟）


@router.post("/schedule/start")
def start_schedule(
    request: ScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    启动定时爬取任务
    """
    schedule_id = f"schedule_{request.crawler_type}"
    
    if scheduler.is_running(schedule_id):
        return {
            "status": "error",
            "message": f"{request.crawler_type} 定时任务已在运行中"
        }
    
    def create_crawler_func():
        from app.database import SessionLocal
        
        def crawler_func():
            db_session = SessionLocal()
            try:
                task_id = task_manager.create_task(
                    CrawlerTaskType(request.crawler_type), 
                    db_session
                )
                crawler_service = CrawlerService(db_session, task_id)
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.running, f"[定时] 开始爬取{request.crawler_type}")
                
                if request.crawler_type == "activities":
                    result = crawler_service.crawl_activities()
                    total = sum(len(v) for v in result.values())
                    task_manager.update_status(task_id, db_session, CrawlerTaskStatus.completed, f"[定时] 完成，共 {total} 个活动")
                elif request.crawler_type == "students":
                    result = crawler_service.crawl_students()
                    task_manager.update_status(task_id, db_session, CrawlerTaskStatus.completed, f"[定时] 完成，共 {len(result)} 个学生")
                elif request.crawler_type == "full":
                    summary = crawler_service.full_crawl(active_statuses=["待开始", "进行中"])
                    task_manager.update_status(
                        task_id, db_session, CrawlerTaskStatus.completed,
                        f"[定时] 综合爬取完成: 活动 {summary.get('activities', 0)} | "
                        f"详情 {summary.get('details', 0)} | 参与者 {summary.get('participants', 0)} 人次"
                    )
                elif request.crawler_type in ("notify_sign", "notify_enrolled", "notify_enrollable"):
                    # 通知类: 需要登录态 driver(复用 CrawlerService 的登录)
                    if not crawler_service.start_driver():
                        task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, "[定时] 登录失败")
                        return
                    driver = crawler_service.driver
                    _log = lambda m: task_manager.append_log(task_id, db_session, m)
                    if request.crawler_type == "notify_sign":
                        from app.services.signin_notify_service import run_sign_notify
                        s = run_sign_notify(db_session, driver, log_fn=_log)
                        msg = f"[定时] 签到{s['sign_in_sent']}/签退{s['sign_out_sent']}, 消息成功{s['msg_success']}"
                    elif request.crawler_type == "notify_enrolled":
                        from app.services.enrolled_notify_service import run_enrolled_notify
                        s = run_enrolled_notify(db_session, driver, log_fn=_log)
                        msg = f"[定时] 报名成功通知{s['sent']}活动, 消息成功{s['msg_success']}"
                    else:  # notify_enrollable
                        from app.services.enrollable_notify_service import run_enrollable_notify
                        s = run_enrollable_notify(db_session, driver, log_fn=_log)
                        msg = f"[定时] 可报名通知{s['sent']}活动, 消息成功{s['msg_success']}"
                    task_manager.update_status(task_id, db_session, CrawlerTaskStatus.completed, msg)
                else:
                    task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, "不支持的类型")
            except Exception as e:
                task_manager.append_log(task_id, db_session, f"[定时] 错误: {str(e)}")
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"[定时] 失败: {str(e)}")
            finally:
                crawler_service.stop_driver()
                db_session.close()
        
        return crawler_func
    
    success = scheduler.start_schedule(
        schedule_id=schedule_id,
        crawler_type=request.crawler_type,
        interval_minutes=request.interval_minutes,
        crawler_func=create_crawler_func()
    )
    
    if success:
        return {
            "status": "success",
            "message": f"{request.crawler_type} 定时任务已启动，间隔 {request.interval_minutes} 分钟",
            "schedule_id": schedule_id
        }
    else:
        return {
            "status": "error",
            "message": "启动定时任务失败"
        }


@router.post("/schedule/stop/{schedule_id}")
def stop_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    停止定时爬取任务
    """
    success = scheduler.stop_schedule(schedule_id)
    
    if success:
        return {
            "status": "success",
            "message": "定时任务已停止"
        }
    else:
        return {
            "status": "error",
            "message": "任务不存在或已停止"
        }


@router.get("/schedule/status")
def get_schedule_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取所有定时任务状态
    """
    return scheduler.get_all_schedules()


@router.get("/schedule/status/{schedule_id}")
def get_single_schedule_status(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取单个定时任务状态
    """
    status = scheduler.get_schedule_status(schedule_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return status


# ==================== 自动化通知脚本API ====================

@router.post("/scripts/new-activity-notify", response_model=TaskStartResponse)
def run_new_activity_notify_script(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    运行新活动报名通知脚本
    - 爬取报名中的活动
    - 发送新活动通知给匹配的学生
    """
    # 创建任务
    task_id = task_manager.create_task(CrawlerTaskType.script_new_activity, db)
    # 立即设置为运行状态
    task_manager.update_status(task_id, db, CrawlerTaskStatus.running, "新活动报名通知脚本启动")

    def run_in_background():
        from app.database import SessionLocal
        from app.scripts.new_activity_notify import NewActivityNotifyScript

        db_session = SessionLocal()
        try:
            task_manager.append_log(task_id, db_session, "=" * 50)
            task_manager.append_log(task_id, db_session, "新活动报名通知脚本开始执行")

            # 检查是否应该停止
            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
                return

            script = NewActivityNotifyScript(db_session, test_mode=False, task_id=task_id, task_manager=task_manager)
            result = script.run()

            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                summary = f"完成: 爬取{result.get('crawled_count', 0)}个活动, 新活动{result.get('new_count', 0)}个, 通知{result.get('notified_count', 0)}个"
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.completed, summary)
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"脚本失败: {str(e)}")
        finally:
            db_session.close()

    background_tasks.add_task(run_in_background)

    return TaskStartResponse(
        task_id=task_id,
        status="started",
        message="新活动报名通知脚本已启动"
    )


@router.post("/scripts/sign-in-notify", response_model=TaskStartResponse)
def run_sign_in_notify_script(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    运行签到通知脚本
    - 爬取进行中的活动
    - 检测签到时间发送通知
    """
    # 创建任务
    task_id = task_manager.create_task(CrawlerTaskType.script_sign_in, db)
    # 立即设置为运行状态
    task_manager.update_status(task_id, db, CrawlerTaskStatus.running, "签到通知脚本启动")

    def run_in_background():
        from app.database import SessionLocal
        from app.scripts.sign_in_notify import SignInNotifyScript

        db_session = SessionLocal()
        try:
            task_manager.append_log(task_id, db_session, "=" * 50)
            task_manager.append_log(task_id, db_session, "签到通知脚本开始执行")

            # 检查是否应该停止
            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
                return

            script = SignInNotifyScript(db_session, test_mode=False, task_id=task_id, task_manager=task_manager)
            result = script.run()

            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                summary = f"完成: 检测{result.get('checked_count', 0)}个活动, 通知{result.get('notified_count', 0)}个"
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.completed, summary)
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"脚本失败: {str(e)}")
        finally:
            db_session.close()

    background_tasks.add_task(run_in_background)

    return TaskStartResponse(
        task_id=task_id,
        status="started",
        message="签到通知脚本已启动"
    )


@router.post("/scripts/sign-out-notify", response_model=TaskStartResponse)
def run_sign_out_notify_script(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    运行签退通知脚本
    - 爬取进行中的活动
    - 检测签退时间发送通知
    """
    # 创建任务
    task_id = task_manager.create_task(CrawlerTaskType.script_sign_out, db)
    # 立即设置为运行状态
    task_manager.update_status(task_id, db, CrawlerTaskStatus.running, "签退通知脚本启动")

    def run_in_background():
        from app.database import SessionLocal
        from app.scripts.sign_out_notify import SignOutNotifyScript

        db_session = SessionLocal()
        try:
            task_manager.append_log(task_id, db_session, "=" * 50)
            task_manager.append_log(task_id, db_session, "签退通知脚本开始执行")

            # 检查是否应该停止
            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
                return

            script = SignOutNotifyScript(db_session, test_mode=False, task_id=task_id, task_manager=task_manager)
            result = script.run()

            if task_manager.should_stop(task_id):
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.stopped, "任务已停止")
            else:
                summary = f"完成: 检测{result.get('checked_count', 0)}个活动, 通知{result.get('notified_count', 0)}个"
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.completed, summary)
        except Exception as e:
            task_manager.append_log(task_id, db_session, f"错误: {str(e)}")
            task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"脚本失败: {str(e)}")
        finally:
            db_session.close()

    background_tasks.add_task(run_in_background)

    return TaskStartResponse(
        task_id=task_id,
        status="started",
        message="签退通知脚本已启动"
    )


# ==================== 脚本定时任务API ====================

@router.post("/scripts/schedule/start")
def start_script_schedule(
    request: ScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    启动脚本定时任务
    支持的脚本类型: script_new_activity, script_sign_in, script_sign_out
    """
    schedule_id = f"schedule_{request.crawler_type}"

    if scheduler.is_running(schedule_id):
        return {
            "status": "error",
            "message": f"{request.crawler_type} 定时任务已在运行中"
        }

    def create_script_func():
        from app.database import SessionLocal

        def script_func():
            db_session = SessionLocal()
            try:
                task_id = task_manager.create_task(
                    CrawlerTaskType(request.crawler_type),
                    db_session
                )
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.running, f"[定时] {request.crawler_type} 启动")

                if request.crawler_type == "script_new_activity":
                    from app.scripts.new_activity_notify import NewActivityNotifyScript
                    script = NewActivityNotifyScript(db_session, test_mode=False, task_id=task_id, task_manager=task_manager)
                    result = script.run()
                    task_manager.update_status(task_id, db_session, CrawlerTaskStatus.completed,
                        f"[定时] 完成: 新活动{result.get('new_count', 0)}个")
                elif request.crawler_type == "script_sign_in":
                    from app.scripts.sign_in_notify import SignInNotifyScript
                    script = SignInNotifyScript(db_session, test_mode=False, task_id=task_id, task_manager=task_manager)
                    result = script.run()
                    task_manager.update_status(task_id, db_session, CrawlerTaskStatus.completed,
                        f"[定时] 完成: 通知{result.get('notified_count', 0)}个")
                elif request.crawler_type == "script_sign_out":
                    from app.scripts.sign_out_notify import SignOutNotifyScript
                    script = SignOutNotifyScript(db_session, test_mode=False, task_id=task_id, task_manager=task_manager)
                    result = script.run()
                    task_manager.update_status(task_id, db_session, CrawlerTaskStatus.completed,
                        f"[定时] 完成: 通知{result.get('notified_count', 0)}个")
                else:
                    task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, "不支持的脚本类型")
            except Exception as e:
                task_manager.append_log(task_id, db_session, f"[定时] 错误: {str(e)}")
                task_manager.update_status(task_id, db_session, CrawlerTaskStatus.failed, f"[定时] 失败: {str(e)}")
            finally:
                db_session.close()

        return script_func

    success = scheduler.start_schedule(
        schedule_id=schedule_id,
        crawler_type=request.crawler_type,
        interval_minutes=request.interval_minutes,
        crawler_func=create_script_func()
    )

    if success:
        return {
            "status": "success",
            "message": f"{request.crawler_type} 定时任务已启动，间隔 {request.interval_minutes} 分钟",
            "schedule_id": schedule_id
        }
    else:
        return {
            "status": "error",
            "message": "启动定时任务失败"
        }
