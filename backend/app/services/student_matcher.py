#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生匹配服务
根据活动的院系、年级限制匹配符合条件的学生
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Student


def parse_colleges(college_name: str) -> List[str]:
    """
    解析可参与院系

    Args:
        college_name: 院系名称字符串，可能包含多个院系，用逗号分隔

    Returns:
        院系列表
    """
    if not college_name:
        return []

    # 处理"不限"的情况
    if "不限" in college_name:
        return ["不限"]

    # 分割并清理
    colleges = [c.strip() for c in college_name.split(",") if c.strip()]
    return colleges


def parse_grades(grade_name: str) -> List[str]:
    """
    解析可参与年级

    Args:
        grade_name: 年级名称字符串，如"2021,2022,2023"

    Returns:
        年级列表
    """
    if not grade_name:
        return []

    # 处理"不限"的情况
    if "不限" in grade_name:
        return ["不限"]

    # 分割并清理
    grades = [g.strip() for g in grade_name.split(",") if g.strip()]
    return grades


def match_students(
    db: Session,
    college_name: str = None,
    grade_name: str = None,
    require_email: bool = True
) -> List[Student]:
    """
    根据条件匹配学生

    Args:
        db: 数据库会话
        college_name: 院系限制
        grade_name: 年级限制
        require_email: 是否要求有邮箱

    Returns:
        符合条件的学生列表
    """
    # 解析条件
    colleges = parse_colleges(college_name)
    grades = parse_grades(grade_name)

    # 构建查询
    query = db.query(Student)

    # 邮箱过滤
    if require_email:
        query = query.filter(Student.email.isnot(None), Student.email != "")

    # 院系过滤
    if colleges and "不限" not in colleges:
        query = query.filter(Student.college_name.in_(colleges))

    # 年级过滤
    if grades and "不限" not in grades:
        query = query.filter(Student.grade_name.in_(grades))

    students = query.all()
    return students


def match_students_for_activity(
    db: Session,
    activity: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    为活动匹配符合条件的学生

    Args:
        db: 数据库会话
        activity: 活动信息字典

    Returns:
        学生信息列表，每个元素包含code, name, email字段
    """
    college_name = activity.get("college_name")
    grade_name = activity.get("grade_name")

    print(f"\n[*] 匹配学生...")
    print(f"    院系限制: {college_name or '不限'}")
    print(f"    年级限制: {grade_name or '不限'}")

    students = match_students(
        db=db,
        college_name=college_name,
        grade_name=grade_name,
        require_email=True
    )

    print(f"    匹配到 {len(students)} 名学生")

    # 转换为字典列表
    result = []
    for student in students:
        result.append({
            "code": student.code,
            "name": student.name,
            "email": student.email,
            "college": student.college_name,
            "grade": student.grade_name
        })

    return result


if __name__ == "__main__":
    # 测试代码
    from app.database import SessionLocal

    db = SessionLocal()

    # 测试解析函数
    print("测试解析院系:")
    colleges = parse_colleges("计算机学院,软件学院")
    print(f"  结果: {colleges}")

    print("\n测试解析年级:")
    grades = parse_grades("2021,2022,2023")
    print(f"  结果: {grades}")

    # 测试匹配学生
    print("\n测试匹配学生:")
    students = match_students(
        db=db,
        college_name="不限",
        grade_name="不限",
        require_email=True
    )
    print(f"  匹配到 {len(students)} 名学生")

    if students:
        print(f"  示例: {students[0].code} - {students[0].name} - {students[0].email}")

    db.close()
