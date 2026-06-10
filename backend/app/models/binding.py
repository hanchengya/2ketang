#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信绑定 + 订阅消息额度 模型

- WxBinding: openid ↔ 学号/工号 的绑定关系,区分 student / admin 角色
  一个 openid 每种角色最多绑一个(支持同一微信既绑本人学号又绑管理员账号)
- SubscribeQuota: 微信订阅消息是"一次授权发一条",这里记每个 openid 对每个模板的剩余可发条数
"""
from sqlalchemy import Column, String, Integer, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class WxBinding(Base):
    """微信用户绑定表"""
    __tablename__ = "wx_bindings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(64), nullable=False, index=True, comment="微信 openid")
    role = Column(String(16), nullable=False, comment="绑定角色: student / admin")
    code = Column(String(32), nullable=False, comment="学号(student) 或 工号(admin)")
    name = Column(String(64), comment="姓名")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="绑定时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        UniqueConstraint("openid", "role", name="uq_binding_openid_role"),
    )

    def __repr__(self):
        return f"<WxBinding(openid={self.openid[:8]}.., role={self.role}, code={self.code})>"


class SubscribeQuota(Base):
    """订阅消息额度表(一次授权 +1, 发送成功 -1)"""
    __tablename__ = "subscribe_quota"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(64), nullable=False, index=True, comment="微信 openid")
    template_id = Column(String(64), nullable=False, comment="订阅消息模板 id")
    remaining = Column(Integer, default=0, comment="剩余可发条数")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        UniqueConstraint("openid", "template_id", name="uq_quota_openid_tmpl"),
    )

    def __repr__(self):
        return f"<SubscribeQuota(openid={self.openid[:8]}.., tmpl={self.template_id[:8]}.., remaining={self.remaining})>"
