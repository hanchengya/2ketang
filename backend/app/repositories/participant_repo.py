#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动参与者 数据访问层
(从 crawler_service._save_participants_to_db 抽出)
"""
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import ActivityParticipant
from app.utils.parse import to_datetime

log = get_logger(__name__)


def save_participants(db: Session, results: List[Dict[str, Any]]) -> int:
    """参与者 upsert。

    results 形如 [{"act_id": int, "participants": [...]}, ...]
    学号/姓名/签到签退字段名有多种别名,逐一兜底。返回保存条数。
    """
    total = 0
    for result in results:
        act_id = result.get("act_id")
        participants = result.get("participants", [])

        for p in participants:
            try:
                student_code = p.get("code") or p.get("studentCode") or p.get("stuCode")
                if not student_code:
                    continue

                sign_in_time = to_datetime(
                    p.get("signInTime") or p.get("sign_in_time") or p.get("inTime")
                )
                sign_out_time = to_datetime(
                    p.get("signOutTime") or p.get("sign_out_time") or p.get("outTime")
                )

                existing = db.query(ActivityParticipant).filter(
                    ActivityParticipant.act_id == act_id,
                    ActivityParticipant.student_code == student_code,
                ).first()

                if existing:
                    existing.sign_in_time = sign_in_time
                    existing.sign_out_time = sign_out_time
                else:
                    db.add(ActivityParticipant(
                        act_id=act_id,
                        student_code=student_code,
                        student_name=p.get("name") or p.get("studentName") or p.get("stuName"),
                        sign_in_time=sign_in_time,
                        sign_out_time=sign_out_time,
                        credits=p.get("credits"),
                    ))
                total += 1
            except Exception:
                log.exception("保存参与者失败 act_id=%s code=%s",
                              act_id, p.get("code") or p.get("studentCode"))

    db.commit()
    return total
