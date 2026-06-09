#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析工具: 时间戳/时间字符串 → datetime
(从 crawler_service._timestamp_to_datetime 抽出,供 repositories 复用)
"""
from datetime import datetime
from typing import Optional


def to_datetime(ts) -> Optional[datetime]:
    """时间戳转 datetime,支持数字时间戳和字符串格式。

    - 多个时间(逗号分隔)取第一个
    - 数字 > 1e10 视为毫秒时间戳
    - 解析失败返回 None
    """
    if not ts:
        return None
    try:
        if isinstance(ts, str) and ',' in ts:
            ts = ts.split(',')[0].strip()

        if isinstance(ts, (int, float)) and ts > 0:
            if ts > 10000000000:
                ts = ts / 1000
            return datetime.fromtimestamp(ts)
        elif isinstance(ts, str):
            ts = ts.strip()
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                try:
                    return datetime.strptime(ts, fmt)
                except ValueError:
                    continue
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except Exception:
        return None
    return None
