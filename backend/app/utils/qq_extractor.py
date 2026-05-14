#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ群号提取工具
"""
import re
from typing import List


def extract_qq_groups(text: str) -> List[str]:
    """
    从文本中提取6-10位连续数字作为QQ群号

    Args:
        text: 待提取的文本

    Returns:
        QQ群号列表
    """
    if not text:
        return []

    # 匹配6-10位连续数字
    pattern = r'\b\d{6,10}\b'
    groups = re.findall(pattern, text)

    # 去重并保持顺序
    seen = set()
    result = []
    for group in groups:
        if group not in seen:
            seen.add(group)
            result.append(group)

    return result


def format_qq_groups(groups: List[str]) -> str:
    """
    格式化QQ群号列表为字符串

    Args:
        groups: QQ群号列表

    Returns:
        格式化后的字符串，用逗号分隔
    """
    if not groups:
        return "暂无"
    return ", ".join(groups)


if __name__ == "__main__":
    # 测试
    test_text = "请加入QQ群：123456789，或者联系987654321，电话：13800138000"
    groups = extract_qq_groups(test_text)
    print(f"提取的QQ群号: {groups}")
    print(f"格式化输出: {format_qq_groups(groups)}")
