#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API
"""
from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.security import verify_password, create_access_token
from app.models import User

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    用户登录

    Args:
        request: 登录请求
        db: 数据库会话

    Returns:
        登录响应（包含JWT token）
    """
    try:
        user = db.query(User).filter(User.username == request.username).first()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="数据库连接失败，请检查数据库配置、账号密码或远程访问权限"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # 创建访问令牌
    access_token = create_access_token(data={"sub": user.username})

    return LoginResponse(
        access_token=access_token,
        username=user.username,
        role=user.role
    )


@router.get("/me", response_model=UserInfo)
def get_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取当前用户信息

    Args:
        current_user: 当前用户

    Returns:
        用户信息
    """
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=bool(current_user.is_active)
    )


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    用户登出

    Args:
        current_user: 当前用户

    Returns:
        成功消息
    """
    return {"message": "Successfully logged out"}
