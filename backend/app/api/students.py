#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生管理API
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_serializer
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import Student, User

router = APIRouter()


class StudentInfo(BaseModel):
    """学生信息"""
    code: str
    name: str
    email: Optional[str] = None
    college_name: Optional[str] = None
    grade_name: Optional[str] = None
    class_name: Optional[str] = None
    mobile: Optional[str] = None
    credit: Optional[Decimal] = None
    sum_score: Optional[Decimal] = None

    class Config:
        from_attributes = True

    @field_serializer('credit', 'sum_score')
    def serialize_decimal(self, v):
        if v is None:
            return None
        return float(v)


class StudentListResponse(BaseModel):
    """学生列表响应"""
    total: int
    items: List[StudentInfo]


class UpdateEmailRequest(BaseModel):
    """更新邮箱请求"""
    email: str


@router.get("", response_model=StudentListResponse)
@router.get("/", response_model=StudentListResponse)
def get_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    keyword: str = Query(""),
    college_name: str = Query(""),
    grade_name: str = Query(""),
    has_email: str = Query(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取学生列表

    Args:
        skip: 跳过数量
        limit: 返回数量
        keyword: 关键字搜索（学号或姓名）
        college_name: 院系筛选
        grade_name: 年级筛选
        has_email: 是否有邮箱
        db: 数据库会话
        current_user: 当前用户

    Returns:
        学生列表
    """
    query = db.query(Student)

    # 筛选条件
    if keyword and keyword.strip():
        query = query.filter(
            (Student.code.like(f"%{keyword}%")) |
            (Student.name.like(f"%{keyword}%"))
        )
    if college_name and college_name.strip():
        query = query.filter(Student.college_name.like(f"%{college_name}%"))
    if grade_name and grade_name.strip():
        query = query.filter(Student.grade_name.like(f"%{grade_name}%"))
    if has_email and has_email.strip():
        if has_email.lower() == "true":
            query = query.filter(Student.email.isnot(None), Student.email != "")
        elif has_email.lower() == "false":
            query = query.filter((Student.email.is_(None)) | (Student.email == ""))

    # 总数
    total = query.count()

    # 分页
    students = query.offset(skip).limit(limit).all()

    # 手动构造StudentInfo对象
    items = []
    for s in students:
        items.append(StudentInfo(
            code=s.code,
            name=s.name,
            email=s.email,
            college_name=s.college_name,
            grade_name=s.grade_name,
            class_name=s.class_name,
            mobile=s.mobile,
            credit=s.credit,
            sum_score=s.sum_score
        ))

    return StudentListResponse(
        total=total,
        items=items
    )


@router.get("/{code}", response_model=StudentInfo)
def get_student(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取学生详情

    Args:
        code: 学号
        db: 数据库会话
        current_user: 当前用户

    Returns:
        学生信息
    """
    student = db.query(Student).filter(Student.code == code).first()
    if not student:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Student not found")

    return StudentInfo.model_validate(student)


@router.put("/{code}/email")
def update_student_email(
    code: str,
    request: UpdateEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新学生邮箱

    Args:
        code: 学号
        request: 更新请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        更新后的学生信息
    """
    student = db.query(Student).filter(Student.code == code).first()
    if not student:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Student not found")

    student.email = request.email
    db.commit()
    db.refresh(student)

    return StudentInfo.model_validate(student)


@router.get("/stats/summary")
def get_student_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取学生统计信息

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        统计信息
    """
    total = db.query(Student).count()
    with_email = db.query(Student).filter(
        Student.email.isnot(None),
        Student.email != ""
    ).count()

    return {
        "total": total,
        "with_email": with_email,
        "without_email": total - with_email
    }
