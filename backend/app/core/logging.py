#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志配置

替代散落各处的 print()。在 main.py 启动时调用 setup_logging() 一次,
之后任何模块 `from app.core.logging import get_logger; log = get_logger(__name__)`。

输出到 stdout(交给 docker 收集),格式带时间/级别/模块:行号,
错误用 log.exception() 可带完整栈(解决之前 str(e) 丢栈的问题)。
"""
import logging
import sys

_CONFIGURED = False


def setup_logging(level: int = None) -> None:
    """配置 root logger。幂等,重复调用只生效一次。"""
    global _CONFIGURED
    if _CONFIGURED:
        return

    # DEBUG 模式更详细,否则 INFO
    from app.config import settings
    log_level = level if level is not None else (logging.DEBUG if settings.DEBUG else logging.INFO)

    root = logging.getLogger()
    root.setLevel(log_level)

    # 清掉可能存在的默认 handler,统一格式
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(handler)

    # 降低三方库噪音
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """获取模块级 logger。"""
    return logging.getLogger(name)
