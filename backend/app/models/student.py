#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生模型
"""
from sqlalchemy import Column, String, Integer, DECIMAL, TIMESTAMP
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.sql import func
from app.database import Base


class Student(Base):
    """学生表"""
    __tablename__ = "students"

    code = Column(String(20), primary_key=True, comment="学号")
    id = Column(Integer, comment="ID")
    name = Column(String(50), comment="姓名")
    gender = Column(TINYINT, comment="性别")
    mobile = Column(String(20), comment="手机号")
    email = Column(String(255), comment="邮箱地址", index=True)

    # 院系信息
    college_id = Column(Integer, comment="院系ID")
    college_name = Column(String(100), comment="院系名称")

    # 年级信息
    grade = Column(Integer, comment="年级")
    grade_name = Column(String(20), comment="年级名称")

    # 班级信息
    class_id = Column(Integer, comment="班级ID")
    class_name = Column(String(50), comment="班级名称")

    # 专业信息
    major_id = Column(Integer, comment="专业ID")
    major_name = Column(String(100), comment="专业名称")

    # 其他信息
    politics = Column(TINYINT, comment="政治面貌")
    ethnic = Column(String(20), comment="民族")
    ethnic_id = Column(Integer, comment="民族ID")
    identity = Column(TINYINT, comment="身份")
    campus_id = Column(Integer, comment="校区ID")
    campus_name = Column(String(100), comment="校区名称")
    length_name = Column(String(20), comment="学制")

    # 学分信息
    credit = Column(DECIMAL(10, 2), comment="学分")
    sum_score = Column(DECIMAL(10, 2), comment="总分")
    user_class_pass = Column(String(10), comment="班级通过")

    # 请假信息
    leave_total_num = Column(Integer, comment="请假总次数")
    leave_success_num = Column(Integer, comment="请假成功次数")
    leave_fail_num = Column(Integer, comment="请假失败次数")

    # 状态
    status = Column(TINYINT, comment="状态")

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Student(code={self.code}, name={self.name}, email={self.email})>"
