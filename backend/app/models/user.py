#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户模型
"""
from sqlalchemy import Column, String, Integer, TIMESTAMP, Enum
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    OPERATOR = "operator"


class User(Base):
    """管理员用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名", index=True)
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    email = Column(String(255), comment="邮箱")
    role = Column(String(20), default="operator", comment="角色")
    is_active = Column(TINYINT, default=1, comment="是否激活")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<User(username={self.username}, role={self.role})>"
