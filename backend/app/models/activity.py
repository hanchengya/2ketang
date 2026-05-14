#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动模型
"""
from sqlalchemy import Column, String, Integer, DECIMAL, DATETIME, TEXT, JSON, TIMESTAMP
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.sql import func
from app.database import Base


class Activity(Base):
    """活动表"""
    __tablename__ = "activities"

    act_id = Column(Integer, primary_key=True, comment="活动ID")
    name = Column(String(500), nullable=False, comment="活动名称")

    # 分类信息
    class_id = Column(Integer, comment="分类ID")
    class_name = Column(String(100), comment="分类名称")

    # 组织信息
    org_id = Column(Integer, comment="组织ID")
    org_name = Column(String(200), comment="组织名称")
    admin_id = Column(Integer, comment="管理员ID")
    admin_code = Column(String(50), comment="管理员代码")
    admin_name = Column(String(100), comment="管理员名称")
    creator_id = Column(Integer, comment="创建者ID")

    # 学时信息
    hours = Column(DECIMAL(5, 2), comment="学时")

    # 时间信息
    start_time = Column(DATETIME, comment="开始时间")
    end_time = Column(DATETIME, comment="结束时间")
    enroll_end_time = Column(DATETIME, comment="报名截止时间")

    # 状态信息
    status = Column(TINYINT, comment="状态")
    apply_status = Column(TINYINT, comment="申请状态")
    status_all = Column(TINYINT, comment="总状态")
    oto = Column(TINYINT, comment="类型标识")
    edit_activity = Column(TINYINT, comment="是否可编辑")
    chenge_status = Column(TINYINT, comment="变更状态")
    finish_status = Column(String(50), comment="完成状态")
    finish_status2 = Column(String(50), comment="完成状态2")

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Activity(act_id={self.act_id}, name={self.name})>"


class ActivityDetail(Base):
    """活动详情表"""
    __tablename__ = "activity_details"

    act_id = Column(Integer, primary_key=True, comment="活动ID")
    act_name = Column(String(500), nullable=False, comment="活动名称")
    introduce = Column(TEXT, comment="活动介绍")

    # 组织信息
    org_id = Column(Integer, comment="组织ID")
    org_name = Column(String(200), comment="组织名称")
    admin_id = Column(Integer, comment="管理员ID")
    admin_name = Column(String(100), comment="管理员名称")
    admin_code = Column(String(50), comment="管理员代码")
    admin_contact = Column(String(50), comment="管理员联系方式")
    creator_id = Column(Integer, comment="创建者ID")
    creator_name = Column(String(100), comment="创建者名称")

    # 活动分类
    class_id = Column(Integer, comment="分类ID")
    class_name = Column(String(100), comment="分类名称")
    type_id = Column(Integer, comment="类型ID")
    type_name = Column(String(200), comment="类型名称")

    # 时间信息
    start_time = Column(DATETIME, comment="开始时间")
    end_time = Column(DATETIME, comment="结束时间")
    enroll_end_time = Column(DATETIME, comment="报名截止时间")
    create_time = Column(DATETIME, comment="创建时间")

    # 活动设置
    hours = Column(DECIMAL(5, 2), comment="学时")
    class_hours = Column(DECIMAL(5, 2), comment="学分")
    people_limit = Column(Integer, comment="人数限制")
    gender = Column(TINYINT, comment="性别限制: 0=不限, 1=男, 2=女")

    # 地点信息
    pitch_id = Column(Integer, comment="场地ID")
    pitch_name = Column(String(200), comment="场地名称")
    pitch_address = Column(String(500), comment="活动地点")

    # 限制条件
    college_ids = Column(TEXT, comment="院系ID列表")
    college_name = Column(String(500), comment="院系名称")
    grade_ids = Column(TEXT, comment="年级ID列表")
    grade_name = Column(String(200), comment="年级名称")
    major_ids = Column(TEXT, comment="专业ID列表")
    major_limit = Column(TEXT, comment="专业限制")
    class_ids = Column(TEXT, comment="班级ID列表")
    class_limit = Column(TEXT, comment="班级限制")
    year_ids = Column(TEXT, comment="学年ID列表")
    year_name = Column(String(200), comment="学年名称")

    # 状态信息
    status_all = Column(TINYINT, comment="总状态")
    apply_status = Column(TINYINT, comment="申请状态")
    chenge_status = Column(TINYINT, comment="变更状态")
    finish_status = Column(String(50), comment="完成状态")
    oto = Column(TINYINT, comment="类型标识")

    # 审核设置
    sign_audit = Column(TINYINT, comment="签到审核")
    expenditure_audit = Column(TINYINT, comment="支出审核")
    audit_flow = Column(JSON, comment="审核流程")

    # 任务设置
    job = Column(TINYINT, comment="任务类型")
    sub_job = Column(TINYINT, comment="子任务")
    teacher_id = Column(Integer, comment="指导教师ID")
    teacher_name = Column(String(100), comment="指导教师姓名")

    # 其他设置
    sign_num = Column(Integer, default=0, comment="签到人数")
    foul_limit = Column(Integer, comment="违规限制")
    expenditure = Column(DECIMAL(10, 2), comment="支出费用")
    logo = Column(String(500), comment="活动图片")
    files = Column(JSON, comment="附件列表")

    # 协办信息
    xieban_id = Column(Integer, comment="协办组织ID")
    xieban_name = Column(String(200), comment="协办组织名称")
    zuzhi_ids = Column(TEXT, comment="组织ID列表")
    zuzhi_name = Column(TEXT, comment="组织名称列表")

    # QQ群信息
    qq_groups = Column(String(500), comment="活动QQ群号")

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="记录创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="记录更新时间")

    def __repr__(self):
        return f"<ActivityDetail(act_id={self.act_id}, act_name={self.act_name})>"
