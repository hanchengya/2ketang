#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "第二课堂活动通知系统API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 导入API路由
from app.api import auth, students, activities, notifications, crawler, wechat, public

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(students.router, prefix="/api/students", tags=["学生管理"])
app.include_router(activities.router, prefix="/api/activities", tags=["活动管理"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["通知管理"])
app.include_router(crawler.router, prefix="/api/crawler", tags=["爬虫控制"])
app.include_router(wechat.router, prefix="/api/wechat", tags=["微信小程序"])
app.include_router(public.router, prefix="/api/public", tags=["公开 API (无认证)"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
