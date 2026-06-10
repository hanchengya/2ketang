#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生信息爬虫模块
"""
import time
import json
import base64
import urllib.parse
import urllib.request
import http.cookiejar
import os
from datetime import datetime
from math import ceil
from typing import List, Dict, Any, Callable, Optional
from selenium.webdriver.common.by import By
from app.crawlers.source_api import source_api_get


# ============ 配置 ============
STUDENT_LIST_URL = "https://2ketangpc.svtcc.edu.cn/student/list?type=4"
SOURCE_API_BASE = "https://2ketangpc.svtcc.edu.cn/manage/server"
PAGE_SIZE = 2000  # 每页条数（网站最大支持2000条）
DEBUG_DIR = "/private/tmp/2ketang-crawler-debug"
# ==============================


def _is_student_item(item: Any) -> bool:
    """判断对象是否像学生记录。"""
    if not isinstance(item, dict):
        return False
    code = item.get("code") or item.get("studentCode") or item.get("stuCode") or item.get("userCode")
    name = item.get("name") or item.get("studentName") or item.get("stuName") or item.get("userName") or item.get("realName")
    return bool(code) and bool(name)


def _normalize_student_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """兼容不同接口字段名，统一为数据库保存需要的 code/name。"""
    normalized = dict(item)
    normalized.setdefault("code", item.get("studentCode") or item.get("stuCode") or item.get("userCode"))
    normalized.setdefault("name", item.get("studentName") or item.get("stuName") or item.get("userName") or item.get("realName"))
    return normalized


def _extract_list_payload(payload: Any) -> Optional[Dict[str, Any]]:
    """从常见接口响应结构中提取 list/total。"""
    if isinstance(payload, list):
        if not payload or _is_student_item(payload[0]):
            return {"items": payload, "total": len(payload)}
        return None

    if not isinstance(payload, dict):
        return None

    candidates = [payload]
    for key in ("data", "result", "payload", "page"):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.append(value)
            nested_data = value.get("data")
            if isinstance(nested_data, dict):
                candidates.append(nested_data)
        elif isinstance(value, list) and (not value or _is_student_item(value[0])):
            total = payload.get("total") or payload.get("count")
            return {"items": value, "total": int(total) if total is not None else len(value)}

    for candidate in candidates:
        for list_key in ("list", "records", "rows", "data", "items", "content"):
            items = candidate.get(list_key)
            if isinstance(items, list) and (not items or _is_student_item(items[0])):
                total = candidate.get("total")
                if total is None:
                    total = candidate.get("count")
                if total is None:
                    total = candidate.get("totalElements")
                if total is None:
                    total = payload.get("total")
                return {
                    "items": items,
                    "total": int(total) if total is not None else len(items)
                }

    return None


def _fetch_json_in_browser(driver, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """用当前浏览器登录态发起同源请求。"""
    script = """
    const done = arguments[arguments.length - 1];
    const url = arguments[0];
    const params = arguments[1];

    const target = new URL(url, window.location.origin);
    Object.keys(params).forEach((key) => {
      if (params[key] !== undefined && params[key] !== null) {
        target.searchParams.set(key, params[key]);
      }
    });

    fetch(target.toString(), {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json, text/plain, */*'
      }
    })
      .then(async (response) => {
        const text = await response.text();
        let data = null;
        try {
          data = JSON.parse(text);
        } catch (error) {
          data = null;
        }
        done({ok: response.ok, status: response.status, url: target.toString(), data});
      })
      .catch((error) => done({ok: false, error: String(error), url: target.toString()}));
    """
    try:
        result = driver.execute_async_script(script, url, params)
        if result and result.get("ok") and result.get("data") is not None:
            return result
    except Exception as e:
        print(f"  接口请求失败 {url}: {e}")
    return None


def _source_api_get(driver, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """使用 Selenium 登录态请求源站接口(薄包装,统一走 source_api,referer 保持学生页)。"""
    return source_api_get(driver, url, params, referer=STUDENT_LIST_URL)


def _save_debug_snapshot(driver, reason: str) -> Optional[str]:
    """保存当前页面截图、HTML、资源列表和 Chrome performance 日志。"""
    try:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(DEBUG_DIR, f"{stamp}_{reason}")
        os.makedirs(output_dir, exist_ok=True)

        screenshot_path = os.path.join(output_dir, "page.png")
        html_path = os.path.join(output_dir, "page.html")
        resources_path = os.path.join(output_dir, "resources.json")
        browser_state_path = os.path.join(output_dir, "browser_state.json")
        performance_path = os.path.join(output_dir, "performance.json")

        driver.save_screenshot(screenshot_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        resources = driver.execute_script("""
            return performance.getEntriesByType('resource').map((entry) => ({
              name: entry.name,
              initiatorType: entry.initiatorType,
              duration: entry.duration,
              transferSize: entry.transferSize
            }));
        """)
        with open(resources_path, "w", encoding="utf-8") as f:
            json.dump(resources, f, ensure_ascii=False, indent=2)

        state = driver.execute_script("""
            return {
              url: location.href,
              title: document.title,
              sessionKey: localStorage.getItem('sessionKey') ? 'present' : 'missing',
              totalText: (document.querySelector('.el-pagination__total') || {}).innerText || '',
              pageInputs: Array.from(document.querySelectorAll('.el-pagination .el-input__inner')).map((el) => el.value),
              bodyTextSample: document.body ? document.body.innerText.slice(0, 2000) : ''
            };
        """)
        with open(browser_state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        try:
            with open(performance_path, "w", encoding="utf-8") as f:
                json.dump(driver.get_log("performance"), f, ensure_ascii=False, indent=2)
        except Exception as e:
            with open(performance_path, "w", encoding="utf-8") as f:
                json.dump({"error": str(e)}, f, ensure_ascii=False, indent=2)

        print(f"  已保存调试现场: {output_dir}")
        return output_dir
    except Exception as e:
        print(f"  保存调试现场失败: {e}")
        return None


def _discover_student_api_urls(driver) -> List[str]:
    """从页面资源记录和常见路径中发现学生列表接口。"""
    script = """
    const staticExt = /\\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|map)(\\?|$)/i;
    const entries = performance.getEntriesByType('resource')
      .map((entry) => entry.name)
      .filter((name) => {
        try {
          const url = new URL(name, window.location.origin);
          return url.origin === window.location.origin
            && !staticExt.test(url.pathname)
            && !/sockjs|hot-update|webpack|vite/i.test(url.pathname);
        } catch (error) {
          return false;
        }
      });
    return Array.from(new Set(entries));
    """
    urls = []
    try:
        urls.extend(driver.execute_script(script) or [])
    except:
        pass

    # 常见路径兜底。真实接口通常会从上面的 performance 记录命中。
    urls.extend([
        "/student",
        "/student/list",
        "/student/page",
        "/students",
        "/students/list",
        "/students/page",
        "/school/students",
        "/school/students/list",
        "/school/students/page",
        "/school/student/list",
        "/school/student/page",
        "/school/students/NoPage",
    ])

    seen = set()
    result = []
    for url in urls:
        normalized = url.split("#", 1)[0]
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def try_crawl_students_by_api(
    driver,
    page_size: int = PAGE_SIZE,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    should_stop_callback: Optional[Callable[[], bool]] = None
) -> Optional[List[Dict[str, Any]]]:
    """优先使用页面背后的接口批量爬取学生信息。失败返回 None。"""
    api_urls = _discover_student_api_urls(driver)
    param_variants = [
        {"current": 1, "size": page_size, "type": 4},
        {"current": 1, "pageSize": page_size, "type": 4},
        {"page": 1, "pageSize": page_size, "type": 4},
        {"page": 1, "limit": page_size, "type": 4},
        {"pageNum": 1, "pageSize": page_size, "type": 4},
        {"currentPage": 1, "pageSize": page_size, "type": 4},
        {"key": "", "current": 1, "size": page_size, "type": 4},
        {"key": "", "page": 1, "pageSize": page_size, "type": 4},
        {"key": ""},
    ]

    selected_url = None
    selected_params = None
    first_items = []
    total = 0

    print("  尝试通过接口批量获取学生数据...")
    print(f"  发现 {len(api_urls)} 个候选接口")
    for url in api_urls[:12]:
        print(f"    候选接口: {url}")

    for url in api_urls:
        for params in param_variants:
            response = _source_api_get(driver, url, params)
            if not response:
                response = _fetch_json_in_browser(driver, url, params)
            if not response:
                continue
            payload = _extract_list_payload(response.get("data"))
            if not payload:
                continue
            items = payload["items"]
            if items and _is_student_item(items[0]):
                selected_url = url
                selected_params = params
                first_items = [_normalize_student_item(item) for item in items]
                total = payload["total"]
                print(f"  命中学生接口: {response.get('url')}")
                print(f"  接口第一页返回 {len(first_items)} 条，总数 {total}")
                break
        if selected_url:
            break

    if not selected_url or not selected_params:
        _save_debug_snapshot(driver, "student_api_not_matched")
        print("  未能自动识别学生接口，退回页面翻页模式")
        return None

    actual_page_size = max(len(first_items), 1)
    total_pages = ceil(total / actual_page_size) if total else 1
    all_students = []
    seen_ids = set()

    def add_items(items: List[Dict[str, Any]]):
        added = 0
        for student in items:
            student = _normalize_student_item(student)
            student_id = student.get("code") or student.get("id")
            if student_id and student_id not in seen_ids:
                seen_ids.add(student_id)
                all_students.append(student)
                added += 1
        return added

    added = add_items(first_items)
    print(f"    第 1/{total_pages} 页获取 {added} 条新数据（累计 {len(all_students)} 条）")
    if progress_callback:
        progress_callback(len(all_students), total)

    for page in range(2, total_pages + 1):
        if should_stop_callback and should_stop_callback():
            print(f"  收到停止信号，已爬取 {len(all_students)} 条")
            break

        params = dict(selected_params)
        for key in ("current", "page", "pageNum", "currentPage"):
            if key in params:
                params[key] = page

        response = _source_api_get(driver, selected_url, params)
        if not response:
            response = _fetch_json_in_browser(driver, selected_url, params)
        if not response:
            print(f"  第 {page} 页接口请求失败，退回页面翻页模式")
            return None

        payload = _extract_list_payload(response.get("data"))
        if not payload:
            print(f"  第 {page} 页接口响应无法识别，退回页面翻页模式")
            return None

        items = payload["items"]
        added = add_items(items)
        print(f"    第 {page}/{total_pages} 页获取 {added} 条新数据（累计 {len(all_students)} 条）")

        if progress_callback:
            progress_callback(len(all_students), total)

        if not items:
            break

    return all_students


def get_page_info(driver) -> Optional[Dict[str, int]]:
    """
    获取分页信息：总条数和总页数

    Args:
        driver: Selenium WebDriver

    Returns:
        分页信息字典
    """
    try:
        script = """
        function findVueData(el) {
            if (el.__vue__) {
                var vm = el.__vue__;
                var data = vm.$data || {};
                if (data.total !== undefined) {
                    return {total: data.total, pageSize: data.pageSize || 10, currentPage: data.currentPage || 1};
                }
            }
            for (var i = 0; i < el.children.length; i++) {
                var result = findVueData(el.children[i]);
                if (result) return result;
            }
            return null;
        }
        return findVueData(document.body);
        """
        info = driver.execute_script(script)
        if info:
            return info
    except:
        pass

    # 备用方案：从DOM获取
    try:
        total_el = driver.find_element(By.CLASS_NAME, "el-pagination__total")
        total_text = total_el.text  # "共 30376 条"
        total = int(''.join(filter(str.isdigit, total_text)))
        return {'total': total, 'pageSize': 10, 'currentPage': 1}
    except:
        return None


def get_current_page_data(
    driver,
    prev_first_id: Optional[int] = None,
    max_wait: int = 15
) -> Optional[List[Dict[str, Any]]]:
    """
    从Vue组件获取当前页的学生数据，确保数据已更新

    Args:
        driver: Selenium WebDriver
        prev_first_id: 前一页第一条数据的ID
        max_wait: 最大等待时间（秒）

    Returns:
        学生数据列表
    """
    # 更全面的数据获取脚本，查找最大的学生数据数组
    script = """
    function findAllStudentData(el, results) {
        results = results || [];
        if (el.__vue__) {
            var vm = el.__vue__;
            var data = vm.$data || {};
            for (var key in data) {
                if (Array.isArray(data[key]) && data[key].length > 0) {
                    var item = data[key][0];
                    if (item && item.code && item.name) {
                        results.push({key: key, data: data[key], len: data[key].length});
                    }
                }
            }
            // 也检查computed属性
            if (vm._computedWatchers) {
                for (var key in vm._computedWatchers) {
                    var val = vm[key];
                    if (Array.isArray(val) && val.length > 0) {
                        var item = val[0];
                        if (item && item.code && item.name) {
                            results.push({key: key, data: val, len: val.length});
                        }
                    }
                }
            }
        }
        for (var i = 0; i < el.children.length; i++) {
            findAllStudentData(el.children[i], results);
        }
        return results;
    }
    var allData = findAllStudentData(document.body, []);
    // 返回最大的数组
    if (allData.length > 0) {
        allData.sort(function(a, b) { return b.len - a.len; });
        return allData[0].data;
    }
    return null;
    """

    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            students = driver.execute_script(script)
            if students and len(students) > 0:
                # 如果指定了prev_first_id，验证首条记录是否已变化
                if prev_first_id is not None:
                    first_id = students[0].get('id')
                    if first_id == prev_first_id:
                        # 数据未更新，继续等待
                        time.sleep(0.5)
                        continue
                return students
        except Exception as e:
            print(f"  获取数据失败: {e}")

        time.sleep(0.5)

    return None


def set_page_size(driver, page_size: int = PAGE_SIZE):
    """
    设置每页显示条数

    Args:
        driver: Selenium WebDriver
        page_size: 每页条数
    """
    from selenium.webdriver.common.keys import Keys
    try:
        print(f"  尝试设置每页 {page_size} 条...")
        
        # 方法1: 通过输入框设置
        try:
            page_input = driver.find_element(By.CSS_SELECTOR, ".el-pagination .el-input__inner")
            if page_input:
                driver.execute_script("arguments[0].scrollIntoView(true);", page_input)
                time.sleep(0.5)
                page_input.click()
                time.sleep(0.3)
                page_input.clear()
                page_input.send_keys(str(page_size))
                page_input.send_keys(Keys.ENTER)
                print(f"    方法1: 输入框设置成功")
                time.sleep(3)
                return
        except Exception as e1:
            print(f"    方法1失败: {e1}")
        
        # 方法2: 通过下拉框选择（如果有2000选项）
        try:
            # 点击下拉框
            select_trigger = driver.find_element(By.CSS_SELECTOR, ".el-pagination .el-select .el-input")
            select_trigger.click()
            time.sleep(0.5)
            
            # 查找2000选项
            options = driver.find_elements(By.CSS_SELECTOR, ".el-select-dropdown__item")
            for option in options:
                if "2000" in option.text:
                    option.click()
                    print(f"    方法2: 下拉框选择成功")
                    time.sleep(3)
                    return
        except Exception as e2:
            print(f"    方法2失败: {e2}")
        
        # 方法3: 直接修改Vue数据
        script = f"""
        // 尝试找到分页组件并修改
        var pagination = document.querySelector('.el-pagination');
        if (pagination) {{
            var app = document.querySelector('#app');
            if (app && app.__vue_app__) {{
                // Vue 3
                var instance = app.__vue_app__._instance;
                if (instance && instance.proxy) {{
                    var proxy = instance.proxy;
                    if (proxy.pageSize !== undefined) {{
                        proxy.pageSize = {page_size};
                        if (proxy.getList) proxy.getList();
                        return 'vue3';
                    }}
                }}
            }}
        }}
        return 'failed';
        """
        result = driver.execute_script(script)
        print(f"    方法3结果: {result}")
        time.sleep(3)
        
    except Exception as e:
        print(f"  设置每页条数失败: {e}")


def go_to_next_page(driver) -> bool:
    """
    点击下一页按钮

    Args:
        driver: Selenium WebDriver

    Returns:
        是否成功
    """
    try:
        script = """
        var nextBtn = document.querySelector('.el-pagination .btn-next');
        if (nextBtn && !nextBtn.classList.contains('disabled')) {
            nextBtn.click();
            return true;
        }
        return false;
        """
        result = driver.execute_script(script)
        if result:
            time.sleep(2)  # 等待页面加载
            return True
    except Exception as e:
        print(f"  翻页失败: {e}")

    return False


def crawl_students(
    driver,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    should_stop_callback: Optional[Callable[[], bool]] = None
) -> List[Dict[str, Any]]:
    """
    爬取所有学生信息

    Args:
        driver: Selenium WebDriver
        progress_callback: 进度回调函数 (current, total)
        should_stop_callback: 停止检查回调函数

    Returns:
        学生数据列表
    """
    print("\n[*] 开始爬取学生信息...")

    # 打开学生列表页面
    driver.get(STUDENT_LIST_URL)
    time.sleep(3)

    # 优化模式：用浏览器登录态直接请求页面背后的分页接口。
    api_students = try_crawl_students_by_api(
        driver,
        PAGE_SIZE,
        progress_callback=progress_callback,
        should_stop_callback=should_stop_callback
    )
    if api_students is not None:
        print(f"\n[*] 学生信息接口爬取完成，共 {len(api_students)} 条")
        return api_students

    # 设置每页显示条数
    set_page_size(driver, PAGE_SIZE)
    time.sleep(2)

    # 获取总数
    page_info = get_page_info(driver)
    if not page_info:
        print("  无法获取分页信息")
        return []

    total = page_info['total']
    print(f"  学生总数: {total}")

    # 先按页面实际分页信息估算总页数；如果设置 2000 条/页失败，
    # 第一页拿到数据后会用真实条数重新计算，避免只爬 16 页。
    actual_page_size = page_info.get('pageSize') or PAGE_SIZE
    total_pages = (total + actual_page_size - 1) // actual_page_size
    print(f"  当前每页条数: {actual_page_size}")
    print(f"  预计共 {total_pages} 页")

    all_students = []
    seen_ids = set()

    # 逐页爬取
    page = 1
    while page <= total_pages:
        # 检查停止信号
        if should_stop_callback and should_stop_callback():
            print(f"  收到停止信号，已爬取 {len(all_students)} 条")
            break

        print(f"  正在爬取第 {page}/{total_pages} 页...")

        # 获取当前页数据
        prev_first_id = all_students[-1]['id'] if all_students else None
        students = get_current_page_data(driver, prev_first_id)

        # 再次检查停止信号
        if should_stop_callback and should_stop_callback():
            print(f"  收到停止信号，已爬取 {len(all_students)} 条")
            break

        if not students:
            print(f"  第 {page} 页数据获取失败")
            break

        # 稳妥模式：以第一页实际返回数量为准重新计算总页数。
        # 有些页面无法真的切到 2000 条/页，如果仍按 2000 计算会漏数据。
        if page == 1 and len(students) > 0:
            real_page_size = len(students)
            if real_page_size != actual_page_size:
                actual_page_size = real_page_size
                total_pages = (total + actual_page_size - 1) // actual_page_size
                print(f"  检测到实际每页 {actual_page_size} 条，修正为共 {total_pages} 页")

        # 去重并添加
        new_count = 0
        for student in students:
            student_id = student.get('id')
            if student_id and student_id not in seen_ids:
                all_students.append(student)
                seen_ids.add(student_id)
                new_count += 1

        print(f"    获取 {new_count} 条新数据（累计 {len(all_students)} 条）")

        # 更新进度
        if progress_callback:
            progress_callback(len(all_students), total)

        # 翻页前检查停止信号
        if should_stop_callback and should_stop_callback():
            print(f"  收到停止信号，已爬取 {len(all_students)} 条")
            break

        # 翻页
        if page < total_pages:
            if not go_to_next_page(driver):
                print(f"  无法翻页，停止爬取")
                break
            time.sleep(1)  # 减少等待时间

        page += 1

    print(f"\n[*] 学生信息爬取完成，共 {len(all_students)} 条")
    return all_students
