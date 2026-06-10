#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信绑定 + 订阅额度 数据访问层
"""
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import WxBinding, SubscribeQuota, Student

log = get_logger(__name__)


# ============ 绑定 ============

def verify_student(db: Session, code: str, name: str) -> bool:
    """校验学号+姓名是否匹配 students 表(student 角色绑定用)。"""
    code = (code or "").strip()
    name = (name or "").strip()
    if not code or not name:
        return False
    stu = db.query(Student).filter(Student.code == code).first()
    return bool(stu and (stu.name or "").strip() == name)


def upsert_binding(db: Session, openid: str, role: str, code: str, name: str) -> WxBinding:
    """绑定/换绑(同一 openid+role 覆盖)。"""
    existing = db.query(WxBinding).filter(
        WxBinding.openid == openid, WxBinding.role == role
    ).first()
    if existing:
        existing.code = code
        existing.name = name
    else:
        existing = WxBinding(openid=openid, role=role, code=code, name=name)
        db.add(existing)
    db.commit()
    return existing


def remove_binding(db: Session, openid: str, role: str) -> bool:
    """解绑。返回是否删除了记录。"""
    n = db.query(WxBinding).filter(
        WxBinding.openid == openid, WxBinding.role == role
    ).delete()
    db.commit()
    return n > 0


def get_bindings(db: Session, openid: str) -> List[WxBinding]:
    """查某 openid 的所有绑定(student / admin)。"""
    return db.query(WxBinding).filter(WxBinding.openid == openid).all()


def openids_by_code(db: Session, code: str, role: str = "student") -> List[str]:
    """按学号/工号反查 openid(发通知时用)。一个学号理论上一个 openid,但返回 list 容错。"""
    rows = db.query(WxBinding).filter(
        WxBinding.code == code, WxBinding.role == role
    ).all()
    return [r.openid for r in rows]


# ============ 订阅额度 ============

def add_quota(db: Session, openid: str, template_id: str, count: int = 1) -> int:
    """订阅授权成功 → 额度 +count。返回新的剩余值。"""
    row = db.query(SubscribeQuota).filter(
        SubscribeQuota.openid == openid, SubscribeQuota.template_id == template_id
    ).first()
    if row:
        row.remaining = (row.remaining or 0) + count
    else:
        row = SubscribeQuota(openid=openid, template_id=template_id, remaining=count)
        db.add(row)
    db.commit()
    return row.remaining


def consume_quota(db: Session, openid: str, template_id: str) -> bool:
    """发送前扣 1 额度。额度不足返回 False(不应发送)。"""
    row = db.query(SubscribeQuota).filter(
        SubscribeQuota.openid == openid, SubscribeQuota.template_id == template_id
    ).first()
    if not row or (row.remaining or 0) <= 0:
        return False
    row.remaining -= 1
    db.commit()
    return True


def get_quota(db: Session, openid: str, template_id: str) -> int:
    row = db.query(SubscribeQuota).filter(
        SubscribeQuota.openid == openid, SubscribeQuota.template_id == template_id
    ).first()
    return (row.remaining or 0) if row else 0
