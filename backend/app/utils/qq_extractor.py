#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
QQ群号提取工具

策略: 上下文优先 + 全局兜底
  1. 先抓"群"关键词 (QQ群 / 一群 / 二群 / 群号 / 加群 ...) 附近的数字, 命中就只用这些
  2. 一个都没命中, 再全局扫所有 5-10 位独立数字 (排除 11 位手机号)

修复历史 bug:
  老正则 `\b\d{6,10}\b` 用了单词边界 \b。中文和数字在正则里都算 \w,
  数字紧贴中文时 (如 "QQ群1105373430参与") 它们之间没有 \b, 导致抓不到。
  只有数字前后是冒号/括号/空格 (非 \w) 时才匹配 —— 这就是"不带冒号的群号读不到"的原因。
  现改用 (?<!\d)\d{5,10}(?!\d): 只要求数字不被更多数字包围, 不依赖单词边界。
"""
import re
from typing import List


# 独立数字串: 前后都不是数字 (允许紧贴中文/字母/标点)
_NUM = r"(?<!\d)(\d{5,11})(?!\d)"

# "群"上下文关键词 (出现这些词时, 其后/周围的数字大概率是群号)
_GROUP_HINT = re.compile(r"(?:QQ群|qq群|Q群|微信群|群\s*号|群\s*[:：]|[一二三四五六七八九1-9]\s*群|加\s*群|入\s*群|交流群|新生群|报名群)")


def _is_plausible_group(num: str) -> bool:
    """一个数字串是否可能是 QQ 群号"""
    # 11 位 1 开头 = 手机号, 排除
    if len(num) == 11 and num.startswith("1"):
        return False
    # QQ 群号常见 5-10 位
    return 5 <= len(num) <= 10


def _dedup(nums: List[str]) -> List[str]:
    seen, out = set(), []
    for n in nums:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def extract_qq_groups(text: str) -> List[str]:
    """
    从文本中提取 QQ 群号。

    Args:
        text: 待提取的文本 (通常是活动简介)

    Returns:
        QQ 群号列表 (去重, 保持出现顺序)
    """
    if not text:
        return []

    # ---- 1. 上下文优先: 抓"群"关键词附近 (关键词后 40 个字符内) 的数字 ----
    context_hits: List[str] = []
    for m in _GROUP_HINT.finditer(text):
        window = text[m.start(): m.end() + 40]
        for num in re.findall(_NUM, window):
            if _is_plausible_group(num):
                context_hits.append(num)

    context_hits = _dedup([n for n in context_hits if _is_plausible_group(n)])
    if context_hits:
        return context_hits

    # ---- 2. 全局兜底: 简介里没有"群"关键词时, 扫所有独立 5-10 位数字 ----
    fallback = [n for n in re.findall(_NUM, text) if _is_plausible_group(n)]
    return _dedup(fallback)


def format_qq_groups(groups: List[str]) -> str:
    """
    格式化 QQ 群号列表为字符串 (逗号分隔)。

    需求文档要求以 "," 分隔, 这里保持纯逗号 (不带空格), 便于前端 split。
    """
    if not groups:
        return ""
    return ",".join(groups)


if __name__ == "__main__":
    tests = [
        "请加入QQ群：1105373430，二群：1105373287",
        "活动QQ群1105373430参与",            # 不带冒号, 数字紧贴中文 (老 bug)
        "群号1234567请尽快加入",
        "咨询电话13800138000",               # 手机号, 应排除
        "QQ群(1030378572)报名",
        "一群123456 二群789012",
        "本活动面向2024级学生, 学号20232818, 请加QQ群987654321",  # 混入年份/学号
        "无任何群信息的简介",
    ]
    for t in tests:
        g = extract_qq_groups(t)
        print(f"{t!r}\n  -> {g}  | 格式化: {format_qq_groups(g)!r}\n")
