#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动爬虫模块
从crawl_activities.py改造而来，支持按标签页爬取
"""
import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from app.config import settings


def click_tab(driver, tab_xpath: str, tab_name: str) -> bool:
    """
    点击标签页

    Args:
        driver: WebDriver实例
        tab_xpath: 标签页的xpath
        tab_name: 标签页名称（用于日志）

    Returns:
        是否成功
    """
    try:
        print(f"[*] 点击 {tab_name} 标签页...")
        tab = driver.find_element(By.XPATH, tab_xpath)
        driver.execute_script("arguments[0].click();", tab)
        time.sleep(settings.CRAWL_DELAY)
        return True
    except Exception as e:
        print(f"    点击 {tab_name} 标签页失败: {e}")
        return False


def set_page_size(driver, size: int) -> bool:
    """设置每页显示条数"""
    try:
        time.sleep(3)
        page_input = driver.find_element(By.CSS_SELECTOR, ".page-input input.el-input__inner")
        driver.execute_script("arguments[0].scrollIntoView(true);", page_input)
        time.sleep(0.5)
        page_input.click()
        time.sleep(0.3)
        # 使用JS直接清空并设置值，避免clear()不生效的问题
        driver.execute_script("arguments[0].value = '';", page_input)
        driver.execute_script(f"arguments[0].value = '{size}';", page_input)
        # 触发input事件让Vue响应
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", page_input)
        print(f"    已输入每页 {size} 条")
        time.sleep(0.5)
        page_input.send_keys(Keys.ENTER)
        print(f"    按回车键触发加载...")
        return True
    except Exception as e:
        print(f"    设置每页条数失败: {e}")
        return False


def get_current_page_data(driver, prev_first_id=None, max_wait=15) -> Optional[List[Dict[str, Any]]]:
    """获取当前页的活动数据"""
    script = """
    function findActivityData(el) {
        if (el.__vue__) {
            var vm = el.__vue__;
            var data = vm.$data || {};
            if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                var item = data.data[0];
                if (item && item.actId && item.name) {
                    return data.data;
                }
            }
        }
        for (var i = 0; i < el.children.length; i++) {
            var result = findActivityData(el.children[i]);
            if (result) return result;
        }
        return null;
    }
    return findActivityData(document.body);
    """

    if prev_first_id:
        print(f"    等待数据更新 (上一页首条ID: {prev_first_id})...")
        for i in range(max_wait):
            data = driver.execute_script(script)
            if data and len(data) > 0:
                current_first_id = data[0].get('actId')
                if current_first_id != prev_first_id:
                    print(f"    数据已更新 (新首条ID: {current_first_id}, 共{len(data)}条)")
                    return data
                else:
                    print(f"    等待中... ({i+1}/{max_wait})")
            time.sleep(1)
        print(f"    警告: 等待{max_wait}秒后数据仍未更新")

    return driver.execute_script(script)


def crawl_activities_by_tab(driver, tab_xpath: str, tab_name: str, prev_first_id: int = None) -> List[Dict[str, Any]]:
    """
    按标签页爬取活动

    Args:
        driver: WebDriver实例
        tab_xpath: 标签页xpath
        tab_name: 标签页名称
        prev_first_id: 上一个标签页的第一条数据ID（用于检测数据是否更新）

    Returns:
        活动列表
    """
    print(f"\n{'='*60}")
    print(f"开始爬取 {tab_name} 活动")
    print(f"{'='*60}")

    # 点击标签页
    if not click_tab(driver, tab_xpath, tab_name):
        return []

    # 设置每页显示条数
    print(f"[*] 设置每页显示 {settings.PAGE_SIZE} 条...")
    if not set_page_size(driver, settings.PAGE_SIZE):
        return []

    # 等待数据加载
    print("    等待数据加载...")
    time.sleep(5)

    # 获取数据（传递上一个标签页的首条ID，确保数据已更新）
    print("[*] 获取活动数据...")
    activities = get_current_page_data(driver, prev_first_id=prev_first_id)

    if activities:
        print(f"    成功获取 {len(activities)} 条活动数据")
        return activities
    else:
        print("    未获取到数据")
        return []


def crawl_all_tabs(driver, stop_check=None) -> Dict[str, List[Dict[str, Any]]]:
    """
    爬取所有标签页的活动

    Args:
        driver: WebDriver实例
        stop_check: 停止检查回调函数，返回True表示应该停止

    Returns:
        字典，键为标签页名称，值为活动列表
    """
    # 访问活动列表页面
    print("\n[1] 访问活动列表页面...")
    driver.get(settings.KETANG_ACTIVITY_URL)
    time.sleep(3)

    result = {}
    prev_first_id = None  # 记录上一个标签页的首条数据ID

    # 定义标签页配置（只爬取报名中和进行中）
    tabs = [
        {"xpath": '//*[@id="tab-4"]', "name": "报名中"},
        {"xpath": '//*[@id="tab-6"]', "name": "进行中"}
    ]

    for tab in tabs:
        # 检查停止信号
        if stop_check and stop_check():
            print("\n[停止] 收到停止信号，中断爬取")
            break

        activities = crawl_activities_by_tab(driver, tab["xpath"], tab["name"], prev_first_id=prev_first_id)
        result[tab["name"]] = activities
        # 记录当前标签页的首条ID，用于下一个标签页检测数据更新
        if activities and len(activities) > 0:
            prev_first_id = activities[0].get('actId')
        time.sleep(2)  # 标签页切换间隔

    return result


def crawl_activities(driver, tabs: List[str] = None, stop_check=None) -> List[Dict[str, Any]]:
    """
    爬取指定标签页的活动（供脚本调用）

    Args:
        driver: WebDriver实例
        tabs: 要爬取的标签页名称列表，如 ["报名中", "进行中"]，默认爬取所有
        stop_check: 停止检查回调函数，返回True表示应该停止

    Returns:
        活动列表
    """
    # 访问活动列表页面
    print("\n[1] 访问活动列表页面...")
    driver.get(settings.KETANG_ACTIVITY_URL)
    time.sleep(3)

    # 标签页配置映射
    tab_config = {
        "报名中": {"xpath": '//*[@id="tab-4"]', "name": "报名中"},
        "进行中": {"xpath": '//*[@id="tab-6"]', "name": "进行中"},
        "待审核": {"xpath": '//*[@id="tab-0"]', "name": "待审核"},
        "已结束": {"xpath": '//*[@id="tab-8"]', "name": "已结束"}
    }

    # 如果没有指定标签页，默认爬取报名中和进行中
    if not tabs:
        tabs = ["报名中", "进行中"]

    all_activities = []
    prev_first_id = None

    for tab_name in tabs:
        # 检查停止信号
        if stop_check and stop_check():
            print("\n[停止] 收到停止信号，中断爬取")
            break

        if tab_name not in tab_config:
            print(f"[警告] 未知的标签页: {tab_name}")
            continue

        tab = tab_config[tab_name]
        activities = crawl_activities_by_tab(driver, tab["xpath"], tab["name"], prev_first_id=prev_first_id)

        # 转换数据格式，添加 act_id 字段（兼容脚本使用）
        for activity in activities:
            activity['act_id'] = activity.get('actId')

        all_activities.extend(activities)

        # 记录当前标签页的首条ID
        if activities and len(activities) > 0:
            prev_first_id = activities[0].get('actId')
        time.sleep(2)

    return all_activities


if __name__ == "__main__":
    from app.crawlers.login import login

    driver = login()
    if driver:
        try:
            result = crawl_all_tabs(driver)
            print("\n" + "="*60)
            print("爬取结果汇总:")
            print("="*60)
            for tab_name, activities in result.items():
                print(f"{tab_name}: {len(activities)} 条活动")
        finally:
            print("\n等待3秒后关闭浏览器...")
            time.sleep(3)
            driver.quit()
