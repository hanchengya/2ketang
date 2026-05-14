#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信小程序 API

- POST /api/wechat/code2session : 用 wx.login 拿到的 code 换 openid
- POST /api/wechat/send         : 下发一条订阅消息
- GET  /api/wechat/token-info   : 调试用, 查看 access_token 缓存状态

注意: 当前接口不带 JWT 鉴权, 仅用于小程序联调。
      上线时可补一个共享密钥 / IP 白名单 / 签名校验。
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services import wechat_service

router = APIRouter()


# ============ 请求 / 响应模型 ============

class Code2SessionRequest(BaseModel):
    code: str = Field(..., description="wx.login() 返回的 code")


class Code2SessionResponse(BaseModel):
    openid: str
    session_key: Optional[str] = None
    unionid: Optional[str] = None


class SendSubscribeRequest(BaseModel):
    touser: str = Field(..., description="接收者的 openid")
    template_id: str = Field(..., description="订阅消息模板 id")
    data: Dict[str, Dict[str, str]] = Field(
        ...,
        description='订阅消息字段, 形如 {"thing1": {"value": "活动名称"}, ...}',
    )
    page: Optional[str] = Field(
        default="pages/notify-test/notify-test",
        description="点击通知跳转的小程序页面",
    )
    miniprogram_state: Optional[str] = Field(
        default=None,
        description="developer / trial / formal, 默认读取配置",
    )
    lang: Optional[str] = Field(default="zh_CN")


# ============ 路由 ============

@router.post("/code2session", response_model=Code2SessionResponse)
def code2session(req: Code2SessionRequest) -> Any:
    """code 换 openid"""
    if not req.code:
        raise HTTPException(status_code=400, detail="code 不能为空")

    try:
        result = wechat_service.code_to_session(req.code)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用微信失败: {e}")

    if "openid" not in result:
        raise HTTPException(status_code=400, detail=result)

    return Code2SessionResponse(
        openid=result["openid"],
        session_key=result.get("session_key"),
        unionid=result.get("unionid"),
    )


@router.post("/send")
def send_subscribe(req: SendSubscribeRequest) -> Any:
    """下发订阅消息

    返回示例 (成功):
        {"errcode": 0, "errmsg": "ok", "msgid": ...}

    常见错误码:
        43101  用户未授权(未弹窗或点了"取消")
        47003  模板参数不合规(字段名不匹配 / 长度超限)
        40037  template_id 不正确
    """
    if not req.touser:
        raise HTTPException(status_code=400, detail="touser 不能为空")
    if not req.template_id:
        raise HTTPException(status_code=400, detail="template_id 不能为空")
    if not req.data:
        raise HTTPException(status_code=400, detail="data 不能为空")

    try:
        result = wechat_service.send_subscribe_message(
            touser=req.touser,
            template_id=req.template_id,
            data=req.data,
            page=req.page,
            miniprogram_state=req.miniprogram_state,
            lang=req.lang or "zh_CN",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用微信失败: {e}")

    # errcode != 0 视为业务失败, 把微信原始响应原样抛出, 方便排查
    if result.get("errcode", 0) != 0:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/token-info")
def token_info() -> Any:
    """查看当前 access_token 缓存状态(便于调试)"""
    return {
        "appid": settings.WECHAT_APPID,
        "miniprogram_state": settings.WECHAT_MINIPROGRAM_STATE,
        "templates": {
            "sign_in": settings.WECHAT_TMPL_SIGN_IN,
        },
        "cache": wechat_service.get_token_info(),
    }
