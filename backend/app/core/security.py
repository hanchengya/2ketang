#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全工具: 密码哈希 + JWT 签发/校验

集中管理,供 api/auth.py、api/deps.py、init_db.py 复用,
避免 bcrypt / jose 调用散落各处、各写一遍。
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt

from app.config import settings


# ============ 密码 ============

def get_password_hash(password: str) -> str:
    """生成 bcrypt 密码哈希"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希是否匹配"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ============ JWT ============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """签发 JWT。默认有效期取 config.ACCESS_TOKEN_EXPIRE_MINUTES。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并校验 JWT。失败抛 jose.JWTError(调用方捕获)。"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
