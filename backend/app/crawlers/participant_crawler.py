#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动参与者爬虫模块
爬取"进行中"活动的"发放学分"页面数据
"""
import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from app.config import settings


ACTIVITY_DETAIL_URL_TEMPLATE = "https://2ketangpc.svtcc.edu.cn/communist/activity/detail?id={}&oto=0&flag=1"


def click_credit_tab(driver) -> bool:
    """
    点击"发放学分"标签

    Args:
        driver: WebDriver实例

    Returns:
        是否成功
    """
    try:
        print("    [*] 点击'发放学分'标签...")
        tab_xpath = '//*[@id="tab-4"]'
        tab = driver.find_element(By.XPATH, tab_xpath)
        driver.execute_script("arguments[0].click();", tab)
        time.sleep(3)
        return True
    except Exception as e:
        print(f"    点击'发放学分'标签失败: {e}")
        return False


def set_participant_page_size(driver, size: int) -> bool:
    """设置参与者列表每页显示条数"""
    try:
        time.sleep(2)
        # 查找页面大小输入框
        page_inputs = driver.find_elements(By.CSS_SELECTOR, ".page-input input.el-input__inner")

        # 通常"发放学分"页面的输入框是第二个
        if len(page_inputs) >= 2:
            page_input = page_inputs[1]
        elif len(page_inputs) == 1:
            page_input = page_inputs[0]
        else:
            print("    未找到页面大小输入框")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", page_input)
        time.sleep(0.5)
        page_input.click()
        time.sleep(0.3)
        page_input.clear()
        time.sleep(0.3)
        page_input.send_keys(str(size))
        print(f"    已输入每页 {size} 条")
        time.sleep(0.5)
        page_input.send_keys(Keys.ENTER)
        print(f"    按回车键触发加载...")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"    设置每页条数失败: {e}")
        return False


def get_participants_data(driver) -> Optional[List[Dict[str, Any]]]:
    """
    获取参与者数据

    Args:
        driver: WebDriver实例

    Returns:
        参与者列表，失败返回None
    """
    script = """
    function findParticipantsData(el) {
        if (el.__vue__) {
            var vm = el.__vue__;
            var data = vm.$data || {};
            
            // 方法1: 查找stuList (发放学分页面常用)
            if (data.stuList && Array.isArray(data.stuList) && data.stuList.length > 0) {
                console.log('Found stuList:', data.stuList.length);
                return data.stuList;
            }
            
            // 方法2: 查找tableData
            if (data.tableData && Array.isArray(data.tableData) && data.tableData.length > 0) {
                console.log('Found tableData:', data.tableData.length);
                return data.tableData;
            }
            
            // 方法3: 查找data数组
            if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                var item = data.data[0];
                if (item && (item.code || item.studentCode || item.name || item.stuCode || item.stuName)) {
                    console.log('Found data array:', data.data.length);
                    return data.data;
                }
            }
            
            // 方法4: 查找list数组
            if (data.list && Array.isArray(data.list) && data.list.length > 0) {
                console.log('Found list:', data.list.length);
                return data.list;
            }
            
            // 方法5: 遍历所有属性查找含有signInTime的数组
            for (var key in data) {
                if (Array.isArray(data[key]) && data[key].length > 0) {
                    var item = data[key][0];
                    if (item && typeof item === 'object') {
                        // 优先查找含有signInTime的数组
                        if (item.signInTime !== undefined || item.signOutTime !== undefined) {
                            console.log('Found array with signInTime in ' + key + ':', data[key].length);
                            return data[key];
                        }
                        if (item.code || item.studentCode || item.name || item.stuName || item.stuCode) {
                            console.log('Found array in ' + key + ':', data[key].length);
                            return data[key];
                        }
                    }
                }
            }
        }
        for (var i = 0; i < el.children.length; i++) {
            var result = findParticipantsData(el.children[i]);
            if (result) return result;
        }
        return null;
    }
    return findParticipantsData(document.body);
    """

    try:
        participants = driver.execute_script(script)
        if participants:
            print(f"    JS脚本找到 {len(participants)} 条数据")
            # 调试：遍历所有记录统计签到签退人数
            if len(participants) > 0:
                first = participants[0]
                keys = list(first.keys()) if isinstance(first, dict) else []
                print(f"    字段: {keys}")
                
                # 打印第一条完整数据用于调试
                if isinstance(first, dict):
                    print(f"    第一条数据样本: {first}")
                
                # 统计签到签退人数 - 检查多种可能的字段名
                sign_in_count = 0
                sign_out_count = 0
                for p in participants:
                    if isinstance(p, dict):
                        # 检查所有可能的签到时间字段名
                        sign_in = p.get("signInTime") or p.get("sign_in_time") or p.get("signinTime") or p.get("signin_time") or p.get("checkInTime") or p.get("inTime")
                        sign_out = p.get("signOutTime") or p.get("sign_out_time") or p.get("signoutTime") or p.get("signout_time") or p.get("checkOutTime") or p.get("outTime")
                        if sign_in:
                            sign_in_count += 1
                        if sign_out:
                            sign_out_count += 1
                print(f"    统计: 总人数={len(participants)}, 已签到={sign_in_count}, 已签退={sign_out_count}")
        else:
            print("    JS脚本未找到数据，尝试备用方法...")
            # 备用方法：查找el-table组件的数据或遍历所有Vue组件
            backup_script = """
            // 方法1: 查找所有Vue组件中的stuList
            function findInAllVue() {
                var elements = document.querySelectorAll('*');
                for (var i = 0; i < elements.length; i++) {
                    var el = elements[i];
                    if (el.__vue__ && el.__vue__.$data) {
                        var data = el.__vue__.$data;
                        if (data.stuList && Array.isArray(data.stuList) && data.stuList.length > 0) {
                            console.log('Backup: Found stuList in element');
                            return data.stuList;
                        }
                    }
                }
                return null;
            }
            
            // 方法2: 从el-table组件获取数据
            function findInTable() {
                var tables = document.querySelectorAll('.el-table');
                for (var i = 0; i < tables.length; i++) {
                    var table = tables[i];
                    if (table.__vue__ && table.__vue__.store) {
                        var store = table.__vue__.store;
                        if (store.states && store.states.data && store.states.data.length > 0) {
                            console.log('Backup: Found data in el-table store');
                            return store.states.data;
                        }
                    }
                }
                return null;
            }
            
            return findInAllVue() || findInTable();
            """
            participants = driver.execute_script(backup_script)
            if participants:
                print(f"    备用方法找到 {len(participants)} 条数据")
                if len(participants) > 0:
                    first = participants[0]
                    print(f"    字段: {list(first.keys()) if isinstance(first, dict) else 'not a dict'}")
                    # 统计签到签退人数
                    sign_in_count = 0
                    sign_out_count = 0
                    for p in participants:
                        if isinstance(p, dict):
                            sign_in = p.get("signInTime") or p.get("sign_in_time") or p.get("inTime")
                            sign_out = p.get("signOutTime") or p.get("sign_out_time") or p.get("outTime")
                            if sign_in:
                                sign_in_count += 1
                            if sign_out:
                                sign_out_count += 1
                    print(f"    统计: 总人数={len(participants)}, 已签到={sign_in_count}, 已签退={sign_out_count}")
        return participants
    except Exception as e:
        print(f"    获取参与者数据失败: {e}")
        return None


def check_sign_in_status(participants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    检查签到/签退状态

    Args:
        participants: 参与者列表

    Returns:
        状态字典，包含has_sign_in和has_sign_out
    """
    has_sign_in = False
    has_sign_out = False

    for participant in participants:
        # 检查签到时间 - 支持多种字段名
        sign_in_time = participant.get("signInTime") or participant.get("sign_in_time") or participant.get("inTime")
        if sign_in_time:
            has_sign_in = True

        # 检查签退时间 - 支持多种字段名
        sign_out_time = participant.get("signOutTime") or participant.get("sign_out_time") or participant.get("outTime")
        if sign_out_time:
            has_sign_out = True

        if has_sign_in and has_sign_out:
            break

    return {
        "has_sign_in": has_sign_in,
        "has_sign_out": has_sign_out
    }


def crawl_activity_participants(driver, act_id: int) -> Optional[Dict[str, Any]]:
    """
    爬取单个活动的参与者信息

    Args:
        driver: WebDriver实例
        act_id: 活动ID

    Returns:
        包含参与者列表和状态的字典，失败返回None
    """
    print(f"\n[*] 爬取活动 {act_id} 的参与者信息...")

    # 访问活动详情页
    url = ACTIVITY_DETAIL_URL_TEMPLATE.format(act_id)
    driver.get(url)
    time.sleep(3)

    # 点击"发放学分"标签
    if not click_credit_tab(driver):
        return None

    # 设置每页显示条数
    print(f"    [*] 设置每页显示 {settings.PARTICIPANT_PAGE_SIZE} 条...")
    if not set_participant_page_size(driver, settings.PARTICIPANT_PAGE_SIZE):
        return None

    # 获取参与者数据
    print("    [*] 获取参与者数据...")
    participants = get_participants_data(driver)

    if not participants:
        print("    未获取到参与者数据，可能该活动没有参与者或页面结构不同")
        # 返回空列表而不是None，这样可以继续处理
        return {
            "act_id": act_id,
            "participants": [],
            "status": {"has_sign_in": False, "has_sign_out": False}
        }

    print(f"    成功获取 {len(participants)} 条参与者数据")

    # 检查签到/签退状态
    status = check_sign_in_status(participants)
    print(f"    签到状态: {'有签到记录' if status['has_sign_in'] else '无签到记录'}")
    print(f"    签退状态: {'有签退记录' if status['has_sign_out'] else '无签退记录'}")

    return {
        "act_id": act_id,
        "participants": participants,
        "status": status
    }


def crawl_participants_batch(driver, act_ids: List[int], stop_check=None, progress_callback=None) -> List[Dict[str, Any]]:
    """
    批量爬取活动参与者信息

    Args:
        driver: WebDriver实例
        act_ids: 活动ID列表
        stop_check: 停止检查回调函数
        progress_callback: 进度回调函数

    Returns:
        参与者信息列表
    """
    total = len(act_ids)
    results = []
    success_count = 0
    fail_count = 0

    print(f"\n{'='*60}")
    print(f"开始爬取 {total} 个活动的参与者信息")
    print(f"{'='*60}")

    for i, act_id in enumerate(act_ids, 1):
        # 检查停止信号
        if stop_check and stop_check():
            print("\n[停止] 收到停止信号，中断爬取")
            break
            
        print(f"\n[{i}/{total}] 活动ID: {act_id}")

        result = crawl_activity_participants(driver, act_id)

        if result:
            results.append(result)
            success_count += 1
            print(f"    [OK] 成功")
        else:
            fail_count += 1
            print(f"    [X] 失败")

        # 更新进度
        if progress_callback:
            progress_callback(i, total)

        # 每5个活动显示一次进度
        if i % 5 == 0:
            print(f"\n进度: {i}/{total} ({i*100//total}%), 成功: {success_count}, 失败: {fail_count}")

        time.sleep(2)  # 避免请求过快

    print(f"\n{'='*60}")
    print(f"爬取完成!")
    print(f"    总计: {total} 个活动")
    print(f"    成功: {success_count} 个")
    print(f"    失败: {fail_count} 个")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    from app.crawlers.login import login

    driver = login()
    if driver:
        try:
            # 测试爬取单个活动的参与者
            test_act_id = 4237
            result = crawl_activity_participants(driver, test_act_id)
            if result:
                print("\n参与者数据:")
                print(f"活动ID: {result['act_id']}")
                print(f"参与者数量: {len(result['participants'])}")
                print(f"签到状态: {result['status']}")
        finally:
            print("\n等待3秒后关闭浏览器...")
            time.sleep(3)
            driver.quit()
