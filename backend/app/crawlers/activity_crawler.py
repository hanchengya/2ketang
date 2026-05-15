#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动爬虫模块

平台 (https://2ketangpc.svtcc.edu.cn/communist/activityDown?oto=0)
活动页有 10 个 tab,这里只关心带状态的 9 个 (tab-1 是"全部",是其它的并集,跳过):

   tab-id     名称          数量级
   tab-2      审核中        几十
   tab-3      被驳回        百级
   tab-4      报名中        几十
   tab-5      待开始        个位
   tab-6      进行中        几十
   tab-7      待完结        百级
   tab-8      完结审核中    百级
   tab-9      完结被驳回    个位
   tab-0      已完结        几千  ← 大头, 需要分页

每个 tab 内的分页处理仿 student_crawler:
  1. 进 tab 后请求 page_size = settings.PAGE_SIZE (2000)
  2. 用首页实际返回数为真实 page_size
  3. 翻页累积 + 按 actId 去重
"""
import time
from typing import List, Dict, Any, Optional, Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from app.config import settings


# (tab_id, 状态名)
# 不包含 tab-1 "全部" (是其它 tab 的并集)
ACTIVITY_TABS = [
    ("tab-2", "审核中"),
    ("tab-3", "被驳回"),
    ("tab-4", "报名中"),
    ("tab-5", "待开始"),
    ("tab-6", "进行中"),
    ("tab-7", "待完结"),
    ("tab-8", "完结审核中"),
    ("tab-9", "完结被驳回"),
    ("tab-0", "已完结"),
]


# ============ 基础动作 ============

def click_tab(driver, tab_id: str, tab_name: str) -> bool:
    """切换到指定 tab"""
    try:
        print(f"[*] 切到 {tab_name} ({tab_id})")
        tab = driver.find_element(By.ID, tab_id)
        driver.execute_script("arguments[0].click();", tab)
        time.sleep(settings.CRAWL_DELAY)
        return True
    except Exception as e:
        print(f"    切换 tab 失败: {e}")
        return False


def set_page_size(driver, size: int) -> bool:
    """请求把活动列表每页条数设为 size。实际是否生效以页面响应为准。"""
    try:
        time.sleep(2)
        page_input = driver.find_element(By.CSS_SELECTOR, ".page-input input.el-input__inner")
        driver.execute_script("arguments[0].scrollIntoView(true);", page_input)
        time.sleep(0.3)
        page_input.click()
        time.sleep(0.2)
        driver.execute_script("arguments[0].value = '';", page_input)
        driver.execute_script(f"arguments[0].value = '{size}';", page_input)
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", page_input
        )
        page_input.send_keys(Keys.ENTER)
        time.sleep(3)
        return True
    except Exception as e:
        print(f"    设置 page_size 失败 (容忍): {e}")
        return False


def get_page_info(driver) -> Optional[Dict[str, Any]]:
    """从激活 tab 的 .el-pagination 读 total / currentPage"""
    script = r"""
    var panes = document.querySelectorAll('.el-tab-pane');
    var pag = null;
    panes.forEach(function(p) {
        if (getComputedStyle(p).display === 'none') return;
        var x = p.querySelector('.el-pagination');
        if (x) pag = x;
    });
    if (!pag) pag = document.querySelector('.el-pagination');
    if (!pag) return null;

    var totalText = (pag.querySelector('.el-pagination__total') || {}).innerText || '';
    var total = parseInt(totalText.replace(/[^0-9]/g, ''), 10);

    var activeLi = pag.querySelector('li.number.active') || pag.querySelector('li.active');
    var currentPage = activeLi ? parseInt(activeLi.innerText, 10) : 1;

    return { total: isNaN(total) ? null : total, currentPage: currentPage };
    """
    try:
        return driver.execute_script(script)
    except Exception:
        return None


def go_to_next_page(driver) -> str:
    """点击激活 tab 内的下一页按钮。返回 'ok' / 'disabled' / 'no-btn'"""
    script = r"""
    var panes = document.querySelectorAll('.el-tab-pane');
    var btn = null;
    panes.forEach(function(p) {
        if (getComputedStyle(p).display === 'none') return;
        var b = p.querySelector('.el-pagination .btn-next');
        if (b) btn = b;
    });
    if (!btn) btn = document.querySelector('.el-pagination .btn-next');
    if (!btn) return 'no-btn';
    if (btn.disabled || btn.classList.contains('disabled') || btn.classList.contains('is-disabled')) {
        return 'disabled';
    }
    btn.click();
    return 'ok';
    """
    try:
        return driver.execute_script(script) or "no-btn"
    except Exception:
        return "no-btn"


# ============ 数据读取 ============

_FIND_ACTIVITY_DATA = r"""
function looksLikeActivity(item) {
    return !!(item && typeof item === 'object' && item.actId && item.name);
}
function collect(el, out) {
    if (el.__vue__) {
        var data = el.__vue__.$data || {};
        for (var k in data) {
            var arr = data[k];
            if (Array.isArray(arr) && arr.length > 0 && looksLikeActivity(arr[0])) {
                out.push({ key: k, data: arr, len: arr.length });
            }
        }
    }
    for (var i = 0; i < el.children.length; i++) collect(el.children[i], out);
}
var out = [];
collect(document.body, out);
if (out.length === 0) return null;
// 取最大数组,防止拿到分页缓存子集
out.sort(function(a, b){ return b.len - a.len; });
return out[0].data;
"""


def get_current_page_data(driver) -> Optional[List[Dict[str, Any]]]:
    try:
        return driver.execute_script("return (function(){" + _FIND_ACTIVITY_DATA + "})()")
    except Exception as e:
        print(f"    读取页面数据失败: {e}")
        return None


def _wait_for_data_change(driver, prev_first_id, max_wait_sec: int = 10) -> Optional[List[Dict[str, Any]]]:
    """等待 vue $data 里首条 actId 与上一页不同。"""
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        rows = get_current_page_data(driver)
        if rows and len(rows) > 0:
            first_id = rows[0].get("actId")
            if prev_first_id is None or first_id != prev_first_id:
                return rows
        time.sleep(0.5)
    return get_current_page_data(driver)


# ============ 单 tab 完整爬取 (带分页) ============

def crawl_one_tab(driver, tab_id: str, tab_name: str, stop_check: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """
    切到指定 tab, 翻完所有页, 返回去重后的活动列表 (每条带 finishStatus = tab_name)。
    """
    print(f"\n{'='*60}")
    print(f"  爬取 {tab_name} ({tab_id})")
    print(f"{'='*60}")

    if not click_tab(driver, tab_id, tab_name):
        return []

    set_page_size(driver, settings.PAGE_SIZE)
    time.sleep(3)

    first_page = get_current_page_data(driver)
    if not first_page:
        print(f"    {tab_name} 无数据")
        return []

    info = get_page_info(driver)
    total = (info or {}).get("total")
    real_page_size = len(first_page)

    if total is None:
        print(f"    读不到 total, 信首页 {real_page_size} 条")
        return _attach_status(first_page, tab_name)

    print(f"    total={total}, 首页 {real_page_size} 条")

    all_acts: List[Dict[str, Any]] = []
    seen = set()

    def add(rows: List[Dict[str, Any]]) -> int:
        added = 0
        for r in rows:
            aid = r.get("actId")
            if aid is None or aid in seen:
                continue
            seen.add(aid)
            all_acts.append(r)
            added += 1
        return added

    add(first_page)

    if len(all_acts) >= total:
        print(f"    首页已覆盖全部 {total} 条")
        return _attach_status(all_acts, tab_name)

    total_pages = (total + real_page_size - 1) // real_page_size if real_page_size else 1
    print(f"    需翻页: 每页 {real_page_size} 条 × {total_pages} 页")

    prev_first_id = first_page[0].get("actId")
    for page_idx in range(2, total_pages + 1):
        if stop_check and stop_check():
            print(f"    收到停止信号,已抓 {len(all_acts)} 条")
            break

        result = go_to_next_page(driver)
        if result != "ok":
            print(f"    第 {page_idx} 页翻页结果: {result}, 终止")
            break

        rows = _wait_for_data_change(driver, prev_first_id, max_wait_sec=10)
        if not rows:
            print(f"    第 {page_idx} 页拿不到数据,终止")
            break

        added = add(rows)
        print(f"    第 {page_idx}/{total_pages} 页新增 {added} (累计 {len(all_acts)}/{total})")
        prev_first_id = rows[0].get("actId")

        if len(all_acts) >= total:
            break

    if len(all_acts) < total:
        print(f"    [WARN] {tab_name} 抓取不完整: {len(all_acts)}/{total}")
    else:
        print(f"    完整抓取 {tab_name}: {len(all_acts)} 条")

    return _attach_status(all_acts, tab_name)


def _attach_status(acts: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
    """给每条活动盖上 finishStatus = 本 tab 状态。覆盖平台返回的 (可能为空的) finishStatus。"""
    for a in acts:
        a["finishStatus"] = status
    return acts


# ============ 入口 ============

def crawl_all_tabs(
    driver,
    stop_check: Optional[Callable] = None,
    tab_ids: Optional[List[str]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    按 tab 爬取所有状态的活动。
    Returns: { 状态名: [活动dict, ...] }
    """
    print("\n[1] 打开活动列表页...")
    driver.get(settings.KETANG_ACTIVITY_URL)
    time.sleep(3)

    targets = ACTIVITY_TABS
    if tab_ids:
        targets = [t for t in ACTIVITY_TABS if t[0] in set(tab_ids)]

    result: Dict[str, List[Dict[str, Any]]] = {}
    for tab_id, tab_name in targets:
        if stop_check and stop_check():
            print("\n[停止] 收到停止信号")
            break
        result[tab_name] = crawl_one_tab(driver, tab_id, tab_name, stop_check)
        time.sleep(1.5)

    # 汇总
    print(f"\n{'='*60}")
    total = 0
    for name, acts in result.items():
        print(f"  {name}: {len(acts)} 条")
        total += len(acts)
    print(f"  合计: {total} 条 (含跨 tab 去重前)")
    print(f"{'='*60}")
    return result


def crawl_activities(
    driver,
    tabs: Optional[List[str]] = None,
    stop_check: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """
    旧入口的兼容版本: 接受状态名列表 (报名中 / 进行中 / 已完结 / ...) 返回扁平列表。

    新代码请优先用 crawl_all_tabs。
    """
    NAME_TO_ID = {name: tid for tid, name in ACTIVITY_TABS}

    if not tabs:
        tabs = ["报名中", "进行中"]

    tab_ids = []
    for name in tabs:
        if name in NAME_TO_ID:
            tab_ids.append(NAME_TO_ID[name])
        else:
            print(f"[警告] 未知 tab 名: {name}")

    grouped = crawl_all_tabs(driver, stop_check=stop_check, tab_ids=tab_ids)

    flat: List[Dict[str, Any]] = []
    for acts in grouped.values():
        for a in acts:
            a.setdefault("act_id", a.get("actId"))
            flat.append(a)
    return flat


if __name__ == "__main__":
    from app.crawlers.login import login

    driver = login()
    if driver:
        try:
            result = crawl_all_tabs(driver)
            print("\n汇总:")
            for name, acts in result.items():
                print(f"  {name}: {len(acts)} 条")
        finally:
            time.sleep(2)
            driver.quit()
