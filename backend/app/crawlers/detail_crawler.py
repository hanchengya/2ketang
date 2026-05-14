#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动详情爬虫模块
从crawl_activity_details.py改造而来
"""
import time
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.qq_extractor import extract_qq_groups, format_qq_groups


ACTIVITY_DETAIL_URL_TEMPLATE = "https://2ketangpc.svtcc.edu.cn/communist/activity/detail?id={}&oto=0&flag=1"


def get_activity_detail_data(driver, act_id: int) -> Optional[Dict[str, Any]]:
    """
    获取活动详情页面的data对象

    Args:
        driver: WebDriver实例
        act_id: 活动ID

    Returns:
        活动详情数据字典，失败返回None
    """
    url = ACTIVITY_DETAIL_URL_TEMPLATE.format(act_id)
    driver.get(url)
    time.sleep(3)

    script = """
    function findActivityDetail(el) {
        if (el.__vue__) {
            var vm = el.__vue__;
            var data = vm.$data || {};
            if (data.data && data.data.actId && data.data.actName) {
                return data.data;
            }
        }
        for (var i = 0; i < el.children.length; i++) {
            var result = findActivityDetail(el.children[i]);
            if (result) return result;
        }
        return null;
    }
    return findActivityDetail(document.body);
    """

    try:
        detail = driver.execute_script(script)
        return detail
    except Exception as e:
        print(f"    获取数据失败: {e}")
        return None


def extract_activity_intro(driver) -> Optional[str]:
    """
    提取活动简介

    Args:
        driver: WebDriver实例

    Returns:
        活动简介文本，失败返回None
    """
    try:
        # 尝试使用xpath提取
        intro_xpath = '//*[@id="app"]/div/div/div[1]/section/div[10]/div/div[10]/span[2]'
        intro_element = driver.find_element("xpath", intro_xpath)
        intro_text = intro_element.text
        return intro_text if intro_text else None
    except Exception as e:
        print(f"    提取活动简介失败: {e}")
        return None


def check_backend_import(introduce: str) -> bool:
    """
    检查活动简介中是否包含"后台导入"关键字

    Args:
        introduce: 活动简介文本

    Returns:
        是否包含"后台导入"
    """
    if not introduce:
        return False
    return "后台导入" in introduce


def enrich_activity_detail(driver, detail: Dict[str, Any]) -> Dict[str, Any]:
    """
    丰富活动详情数据（提取QQ群、检测后台导入等）

    Args:
        driver: WebDriver实例
        detail: 原始活动详情数据

    Returns:
        丰富后的活动详情数据
    """
    # 提取活动简介（如果原数据中没有）
    if not detail.get("introduce"):
        intro = extract_activity_intro(driver)
        if intro:
            detail["introduce"] = intro

    # 提取QQ群号
    introduce = detail.get("introduce", "")
    qq_groups = extract_qq_groups(introduce)
    detail["qq_groups"] = format_qq_groups(qq_groups)
    detail["qq_groups_list"] = qq_groups

    # 检测后台导入
    detail["is_backend_import"] = check_backend_import(introduce)

    return detail


def crawl_activity_detail(driver, act_id: int) -> Optional[Dict[str, Any]]:
    """
    爬取单个活动的详情

    Args:
        driver: WebDriver实例
        act_id: 活动ID

    Returns:
        活动详情数据，失败返回None
    """
    print(f"\n[*] 爬取活动 {act_id} 的详情...")

    # 获取基础数据
    detail = get_activity_detail_data(driver, act_id)
    if not detail:
        print(f"    获取活动 {act_id} 数据失败")
        return None

    print(f"    活动名称: {detail.get('actName', '未知')}")

    # 丰富数据
    detail = enrich_activity_detail(driver, detail)

    # 输出关键信息
    if detail.get("is_backend_import"):
        print(f"    ⚠️  检测到'后台导入'，建议跳过此活动")

    if detail.get("qq_groups_list"):
        print(f"    QQ群: {detail.get('qq_groups')}")

    return detail


def crawl_activity_details(driver, act_ids: list, stop_check=None, progress_callback=None) -> list:
    """
    批量爬取活动详情

    Args:
        driver: WebDriver实例
        act_ids: 活动ID列表
        stop_check: 停止检查回调函数
        progress_callback: 进度回调函数

    Returns:
        活动详情列表
    """
    total = len(act_ids)
    details = []
    success_count = 0
    fail_count = 0

    print(f"\n{'='*60}")
    print(f"开始爬取 {total} 个活动的详情")
    print(f"{'='*60}")

    for i, act_id in enumerate(act_ids, 1):
        # 检查停止信号
        if stop_check and stop_check():
            print("\n[停止] 收到停止信号，中断爬取")
            break
            
        print(f"\n[{i}/{total}] 活动ID: {act_id}")

        detail = crawl_activity_detail(driver, act_id)

        if detail:
            details.append(detail)
            success_count += 1
            print(f"    [OK] 成功")
        else:
            fail_count += 1
            print(f"    [X] 失败")

        # 更新进度
        if progress_callback:
            progress_callback(i, total)

        # 每10个活动显示一次进度
        if i % 10 == 0:
            print(f"\n进度: {i}/{total} ({i*100//total}%), 成功: {success_count}, 失败: {fail_count}")

        time.sleep(1)  # 避免请求过快

    print(f"\n{'='*60}")
    print(f"爬取完成!")
    print(f"    总计: {total} 个活动")
    print(f"    成功: {success_count} 个")
    print(f"    失败: {fail_count} 个")
    print(f"{'='*60}")

    return details


if __name__ == "__main__":
    from app.crawlers.login import login

    driver = login()
    if driver:
        try:
            # 测试爬取单个活动
            test_act_id = 4237
            detail = crawl_activity_detail(driver, test_act_id)
            if detail:
                print("\n详情数据:")
                print(f"活动名称: {detail.get('actName')}")
                print(f"活动简介: {detail.get('introduce', '无')[:100]}...")
                print(f"QQ群: {detail.get('qq_groups')}")
                print(f"后台导入: {detail.get('is_backend_import')}")
        finally:
            print("\n等待3秒后关闭浏览器...")
            time.sleep(3)
            driver.quit()
