#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
源站 API 公共调用层

第二课堂前端所有数据接口都在 /manage/server 下,鉴权方式统一:
  - 从浏览器 localStorage.sessionKey 取 token
  - Authorization = AES-ECB(key=xiangfubeitu2025) 加密 {"token","platform":3,"timestamp"}
  - 带浏览器 cookie
  - 参数包成 ?params={json}

(从 student_crawler 抽出,供 student / activity 等所有 API 爬取复用。
 Selenium 只负责登录拿 sessionKey+cookie,之后纯 HTTP,速度远超页面翻页。)
"""
import base64
import http.cookiejar
import json
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from app.core.logging import get_logger

log = get_logger(__name__)

SOURCE_API_BASE = "https://2ketangpc.svtcc.edu.cn/manage/server"
DEFAULT_REFERER = "https://2ketangpc.svtcc.edu.cn/"
_AES_KEY = "xiangfubeitu2025".encode("utf-8")


def _pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    padding = block_size - (len(data) % block_size)
    return data + bytes([padding]) * padding


def encrypt_authorization(text: str) -> str:
    """复刻第二课堂前端的 CryptoJS AES-ECB Authorization 签名。"""
    cipher = Cipher(algorithms.AES(_AES_KEY), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(_pkcs7_pad(text.encode("utf-8"))) + encryptor.finalize()
    return base64.b64encode(encrypted).decode("utf-8")


def _build_cookie_jar(driver) -> http.cookiejar.CookieJar:
    jar = http.cookiejar.CookieJar()
    for cookie in driver.get_cookies():
        jar.set_cookie(http.cookiejar.Cookie(
            version=0,
            name=cookie.get("name"),
            value=cookie.get("value"),
            port=None,
            port_specified=False,
            domain=cookie.get("domain"),
            domain_specified=bool(cookie.get("domain")),
            domain_initial_dot=(cookie.get("domain") or "").startswith("."),
            path=cookie.get("path", "/"),
            path_specified=True,
            secure=bool(cookie.get("secure")),
            expires=cookie.get("expiry"),
            discard=False,
            comment=None,
            comment_url=None,
            rest={},
            rfc2109=False,
        ))
    return jar


def source_api_get(
    driver,
    url: str,
    params: Dict[str, Any],
    referer: str = DEFAULT_REFERER,
    timeout: int = 30,
) -> Optional[Dict[str, Any]]:
    """用 Selenium 登录态直接 GET 源站 /manage/server 接口。

    Args:
        url: 接口路径(如 "/activity/actAllList")或完整 URL
        params: 业务参数(会被包成 ?params={json})
        referer: 请求 Referer(平台内页即可)
    Returns:
        {"ok","status","url","data"} 或 None(失败)
    """
    try:
        session_key = driver.execute_script("return localStorage.getItem('sessionKey') || '';") or ""
        if not session_key:
            log.warning("未获取到 sessionKey,无法调用源站接口")
            return None

        timestamp = int(time.time() * 1000)
        auth_payload = json.dumps(
            {"token": session_key, "platform": 3, "timestamp": timestamp},
            separators=(",", ":"), ensure_ascii=False,
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": encrypt_authorization(auth_payload),
            "User-Agent": driver.execute_script("return navigator.userAgent;") or "Mozilla/5.0",
            "Referer": referer,
            "Accept": "application/json, text/plain, */*",
        }

        target_url = url
        if target_url.startswith("/"):
            target_url = SOURCE_API_BASE + target_url
        elif target_url.startswith("http") and "/manage/server" not in target_url:
            parsed_path = "/" + target_url.split("://", 1)[1].split("/", 1)[1]
            target_url = SOURCE_API_BASE + parsed_path

        # 剥掉 URL 自带的旧 query
        parsed = urllib.parse.urlsplit(target_url)
        target_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))

        query = urllib.parse.urlencode({
            "params": json.dumps(params, separators=(",", ":"), ensure_ascii=False)
        })
        sep = "&" if "?" in target_url else "?"
        request_url = f"{target_url}{sep}{query}"

        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(_build_cookie_jar(driver))
        )
        req = urllib.request.Request(request_url, headers=headers, method="GET")
        with opener.open(req, timeout=timeout) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8")
        if status < 200 or status >= 300:
            log.warning("源站接口 %s 返回 %s", target_url, status)
            return None
        return {"ok": True, "status": status, "url": request_url, "data": json.loads(body)}
    except Exception:
        log.exception("源站接口请求异常 %s", url)
        return None
