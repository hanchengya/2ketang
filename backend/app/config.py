#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """系统配置"""

    # 应用配置
    APP_NAME: str = "第二课堂活动通知系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DB_HOST: str = "10.5.80.8"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "2ketang"
    DB_CHARSET: str = "utf8mb4"

    @property
    def DATABASE_URL(self) -> str:
        """数据库连接URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"

    # 邮箱配置
    SMTP_SERVER: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SENDER_EMAIL: str = "lcxlio@qq.com"
    EMAIL_AUTH_CODE: str = "vxxzxmrcnzbvddde"
    SENDER_NAME: str = "数智维新工作室"

    # 系统配置
    TEST_MODE: bool = True  # 测试模式（不实际发送邮件）
    CRAWL_DELAY: int = 5  # 爬取延迟（秒）
    EMAIL_DELAY: int = 1  # 邮件发送延迟（秒）
    PAGE_SIZE: int = 2000  # 活动列表每页条数
    PARTICIPANT_PAGE_SIZE: int = 2000  # 参与者列表每页条数

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # 第二课堂登录配置
    KETANG_USERNAME: str = "2004"
    KETANG_PASSWORD: str = "yxsh2004,,."
    KETANG_LOGIN_URL: str = "https://2ketangpc.svtcc.edu.cn/login"
    KETANG_ACTIVITY_URL: str = "https://2ketangpc.svtcc.edu.cn/communist/activityDown?oto=0"

    # 微信小程序配置（订阅消息）
    WECHAT_APPID: str = "wx3332c07f6d4cf60a"
    WECHAT_SECRET: str = ""  # 在 .env 中填入小程序 AppSecret
    WECHAT_MINIPROGRAM_STATE: str = "developer"  # developer / trial / formal
    # 已申请的订阅消息模板
    WECHAT_TMPL_SIGN_IN: str = "W4OsGLrQL8YcBFsdTtaYDLdfE4gkqkT0Q1jZdpNuUs4"

    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177", "http://localhost:5178", "http://localhost:5179", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5179"]

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
