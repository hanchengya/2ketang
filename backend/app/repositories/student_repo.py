#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生 数据访问层
(从 crawler_service._save_students_to_db 抽出)

学生量大(3万+),用 MySQL 的 INSERT ... ON DUPLICATE KEY UPDATE 分批 upsert。
"""
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import Student

log = get_logger(__name__)


def _clean(value):
    return None if value == "" else value


def _build_values(student: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    code = str(student.get("code") or "").strip()
    if not code:
        return None
    return {
        "code": code,
        "id": _clean(student.get("id")),
        "name": _clean(student.get("name")),
        "gender": _clean(student.get("gender")),
        "ethnic": _clean(student.get("ethnic")),
        "politics": _clean(student.get("politics")),
        "mobile": _clean(student.get("mobile")),
        "campus_id": _clean(student.get("campusId")),
        "campus_name": _clean(student.get("campusName")),
        "college_id": _clean(student.get("collegeId")),
        "college_name": _clean(student.get("collegeName")),
        "major_id": _clean(student.get("majorId")),
        "major_name": _clean(student.get("majorName")),
        "class_id": _clean(student.get("classId")),
        "class_name": _clean(student.get("className")),
        "grade": _clean(student.get("grade")),
        "grade_name": _clean(student.get("gradeName")),
        "length_name": _clean(student.get("lengthName")),
        "credit": _clean(student.get("credit")),
        "sum_score": _clean(student.get("sumScore")),
        "user_class_pass": _clean(student.get("userClassPass")),
        "status": _clean(student.get("status")),
        "leave_total_num": _clean(student.get("leaveTotalNum")),
        "leave_success_num": _clean(student.get("leaveSuccessNum")),
        "leave_fail_num": _clean(student.get("leaveFailNum")),
    }


def save_students(
    db: Session,
    students: List[Dict[str, Any]],
    batch_size: int = 500,
    should_stop: Optional[Callable[[], bool]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> int:
    """分批 upsert 学生。

    should_stop(): 可选,返回 True 则中断(已 commit 的批保留)。
    on_progress(saved, total): 可选进度回调。
    返回保存条数。
    """
    total_saved = 0
    total = len(students)

    def save_batch(batch: List[Dict[str, Any]]) -> int:
        if not batch:
            return 0
        stmt = mysql_insert(Student).values(batch)
        update_values = {k: stmt.inserted[k] for k in batch[0].keys() if k != "code"}
        db.execute(stmt.on_duplicate_key_update(**update_values))
        return len(batch)

    batch: List[Dict[str, Any]] = []
    for student in students:
        if should_stop and should_stop():
            break
        try:
            values = _build_values(student)
            if not values:
                continue
            batch.append(values)
            if len(batch) >= batch_size:
                total_saved += save_batch(batch)
                db.commit()
                batch = []
                if on_progress and total_saved % 5000 == 0:
                    on_progress(total_saved, total)
        except Exception:
            db.rollback()
            log.exception("保存学生失败 code=%s", student.get("code"))
            batch = []

    if batch:
        total_saved += save_batch(batch)
    db.commit()
    return total_saved
