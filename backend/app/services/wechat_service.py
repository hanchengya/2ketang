#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信小程序服务

- 维护 access_token 的内存缓存(线程安全, 1 小时过期前 60s 主动刷新)
- 封装 code2session、订阅消息下发两个常用接口

仅使用 Python 标准库(urllib + json), 不引入新依赖
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from threading import Lock
from typing import Any, Dict, Optional

from app.config import settings


# ============ HTTP 工具 ============

def _http_get_json(url: str, timeout: int = 10) -> Dict[str, Any]:
    """GET 一个 URL 并解析 JSON 响应"""
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def _http_post_json(url: str, payload: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """POST JSON body 并解析响应"""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


# ============ access_token 缓存 ============

class WechatAccessTokenCache:
    """线程安全的 access_token 缓存

    微信文档: https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/mp-access-token/getAccessToken.html
    - access_token 有效期 7200s
    - 同一 appid 不要并发刷新
    """

    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._expire_at: float = 0.0
        self._lock = Lock()

    def get(self, force_refresh: bool = False) -> str:
        with self._lock:
            now = time.time()
            if (not force_refresh
                    and self._token
                    and now < self._expire_at - 60):
                return self._token

            if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
                raise RuntimeError(
                    "WECHAT_APPID 或 WECHAT_SECRET 未配置, 请检查 .env"
                )

            url = (
                "https://api.weixin.qq.com/cgi-bin/token"
                "?grant_type=client_credential"
                f"&appid={urllib.parse.quote(settings.WECHAT_APPID)}"
                f"&secret={urllib.parse.quote(settings.WECHAT_SECRET)}"
            )
            data = _http_get_json(url)

            if "access_token" not in data:
                raise RuntimeError(f"获取 access_token 失败: {data}")

            self._token = data["access_token"]
            self._expire_at = now + int(data.get("expires_in", 7200))
            return self._token

    def info(self) -> Dict[str, Any]:
        """便于调试: 返回当前缓存状态"""
        return {
            "cached": bool(self._token),
            "expire_at": self._expire_at,
            "remaining_seconds": max(0, int(self._expire_at - time.time())),
        }


_cache = WechatAccessTokenCache()


# ============ 业务封装 ============

def code_to_session(code: str) -> Dict[str, Any]:
    """code 换 openid + session_key

    微信文档: https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/login/auth.code2Session.html
    """
    if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
        raise RuntimeError("WECHAT_APPID 或 WECHAT_SECRET 未配置, 请检查 .env")

    url = (
        "https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={urllib.parse.quote(settings.WECHAT_APPID)}"
        f"&secret={urllib.parse.quote(settings.WECHAT_SECRET)}"
        f"&js_code={urllib.parse.quote(code)}"
        "&grant_type=authorization_code"
    )
    return _http_get_json(url)


def send_subscribe_message(
    touser: str,
    template_id: str,
    data: Dict[str, Dict[str, str]],
    page: Optional[str] = None,
    miniprogram_state: Optional[str] = None,
    lang: str = "zh_CN",
) -> Dict[str, Any]:
    """下发一条订阅消息

    微信文档: https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/mp-message-management/subscribe-message/sendMessage.html

    Args:
        touser: 接收者的 openid
        template_id: 订阅消息模板 id
        data: {"thing1": {"value": "..."}, ...}
        page: 小程序跳转页面, 例如 "pages/notify-test/notify-test"
        miniprogram_state: developer / trial / formal, 不传则用 settings 默认值
        lang: 语言, 默认 zh_CN
    """
    token = _cache.get()
    url = (
        "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"
        f"?access_token={urllib.parse.quote(token)}"
    )

    payload: Dict[str, Any] = {
        "touser": touser,
        "template_id": template_id,
        "data": data,
        "miniprogram_state": miniprogram_state or settings.WECHAT_MINIPROGRAM_STATE,
        "lang": lang,
    }
    if page:
        payload["page"] = page

    result = _http_post_json(url, payload)

    # 如果 access_token 过期 (errcode=40001/42001), 主动刷新一次重试
    if result.get("errcode") in (40001, 42001):
        token = _cache.get(force_refresh=True)
        url = (
            "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"
            f"?access_token={urllib.parse.quote(token)}"
        )
        result = _http_post_json(url, payload)

    return result


def get_token_info() -> Dict[str, Any]:
    """供调试接口使用"""
    return _cache.info()
