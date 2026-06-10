#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件

【安全约定】敏感项(密码/密钥/授权码)一律从环境变量或 .env 注入,代码里不写真实值:
  - DB_PASSWORD / SECRET_KEY  : 必填(无默认),缺失则启动失败(fail-fast,杜绝弱默认值兜底)
  - EMAIL_AUTH_CODE / KETANG_USERNAME / KETANG_PASSWORD / WECHAT_SECRET : 可空,
    留空则对应功能(邮件/爬虫/微信)不可用,但不阻塞主服务启动

生产环境通过 docker-compose 的 environment 段注入(值来自 admin/.env)。
本地开发: 复制 .env.example 为 .env 并填值。
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """系统配置"""

    # 应用配置
    APP_NAME: str = "第二课堂活动通知系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # 生产默认关闭,避免泄露堆栈

    # 数据库配置
    DB_HOST: str = "10.5.80.8"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str  # 必填,从环境变量 / .env 注入
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
    EMAIL_AUTH_CODE: str = ""  # QQ邮箱授权码,从 .env 注入(空则邮件功能不可用)
    SENDER_NAME: str = "数智维新工作室"

    # 系统配置
    TEST_MODE: bool = True  # 测试模式（不实际发送邮件）
    CRAWL_DELAY: int = 5  # 爬取延迟（秒）
    EMAIL_DELAY: int = 1  # 邮件发送延迟（秒）
    PAGE_SIZE: int = 2000  # 活动列表每页条数
    PARTICIPANT_PAGE_SIZE: int = 2000  # 参与者列表每页条数
    SIGN_NOTIFY_THRESHOLD: int = 2  # 签到/签退通知触发阈值(已签到/签退人数 ≥ 此值才发)

    # JWT配置
    SECRET_KEY: str  # 必填,从环境变量 / .env 注入(JWT 签名密钥)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # 第二课堂登录配置
    KETANG_USERNAME: str = ""  # 爬虫账号,从 .env 注入(空则爬虫不可用)
    KETANG_PASSWORD: str = ""  # 爬虫密码,从 .env 注入
    KETANG_LOGIN_URL: str = "https://2ketangpc.svtcc.edu.cn/login"
    KETANG_ACTIVITY_URL: str = "https://2ketangpc.svtcc.edu.cn/communist/activityDown?oto=0"

    # 微信小程序配置（订阅消息）
    WECHAT_APPID: str = "wx3332c07f6d4cf60a"  # 小程序 AppID(公开值)
    WECHAT_SECRET: str = ""  # 小程序 AppSecret,从 .env 注入
    WECHAT_MINIPROGRAM_STATE: str = "developer"  # developer / trial / formal

    # 订阅消息模板(template_id,公开值,可留默认)
    # A 活动参与通知: thing1 活动名/time2 时间/thing4 地址/thing5 活动对象
    #   → 报名成功 / 请签到 / 请签退(靠 thing5 区分)
    WECHAT_TMPL_ACTIVITY: str = "uH5KwbIubW0QmpFdS2QCQwjmRhaljivu7C_3zGL1LKw"
    # B 审核通过通知: thing15 任务名/thing5 备注/phrase1 审核结果 → 管理员/老师
    WECHAT_TMPL_REVIEW: str = "jxH94kFO-hzvfF7R58_z5GYrXKS-yKLcSeNAFETXIMA"
    # C 报名时间提醒: thing9 活动名/time6 开始/time7 截止/thing3 温馨提示 → 可报名
    WECHAT_TMPL_ENROLL: str = "FpCTZJMYpLFmxMWFizluEv0qF3ymoaFgdoVeobTksJQ"
    # (旧)签到提醒,已被 A 模板取代,保留兼容
    WECHAT_TMPL_SIGN_IN: str = "W4OsGLrQL8YcBFsdTtaYDLdfE4gkqkT0Q1jZdpNuUs4"

    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177", "http://localhost:5178", "http://localhost:5179", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5179"]

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
