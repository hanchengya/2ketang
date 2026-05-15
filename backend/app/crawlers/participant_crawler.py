#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动参与者爬虫模块
爬取"进行中"活动"发放学分"页面的全部参与者数据。

历史 bug:
  - 老版本设置每页 2000 条后直接读 Vue stuList,假定一次性拿到全部,
    但第二课堂平台对 page_size 通常有上限(实测 100~500),
    导致大活动只拿到首页前 100 条,剩下的静默丢失。
  - 老版本也没有翻页循环。

修复:
  - 从 .el-pagination 读取总条数 total
  - 以首页实际返回长度为真实 page_size,如果 != 2000 自动重算总页数
  - 用 .btn-next 逐页翻,每页都去重 + 合并
  - 收尾对比 total vs 实际抓到的数量,不一致打 WARN
"""
import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from app.config import settings


ACTIVITY_DETAIL_URL_TEMPLATE = "https://2ketangpc.svtcc.edu.cn/communist/activity/detail?id={}&oto=0&flag=1"


def click_credit_tab(driver) -> bool:
    """点击'发放学分'标签 (tab-4)"""
    try:
        print("    [*] 点击'发放学分'标签...")
        tab = driver.find_element(By.XPATH, '//*[@id="tab-4"]')
        driver.execute_script("arguments[0].click();", tab)
        time.sleep(3)
        return True
    except Exception as e:
        print(f"    点击'发放学分'标签失败: {e}")
        return False


def set_participant_page_size(driver, size: int) -> bool:
    """
    设置参与者列表每页条数。
    返回是否触发了一次输入 + 回车(不保证 size 被服务端接受)。
    """
    try:
        time.sleep(2)
        page_inputs = driver.find_elements(By.CSS_SELECTOR, ".page-input input.el-input__inner")
        # 发放学分页面通常有多个 page-input,取第二个;只有一个就用第一个
        if len(page_inputs) >= 2:
            page_input = page_inputs[1]
        elif len(page_inputs) == 1:
            page_input = page_inputs[0]
        else:
            print("    未找到 page-input 输入框,跳过 page_size 设置")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", page_input)
        time.sleep(0.3)
        page_input.click()
        time.sleep(0.2)
        page_input.clear()
        time.sleep(0.2)
        page_input.send_keys(str(size))
        page_input.send_keys(Keys.ENTER)
        print(f"    已请求每页 {size} 条 (实际值取决于平台上限)")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"    设置每页条数失败: {e}")
        return False


# ============ 数据获取 ============

# 公用 JS 片段:在整个 DOM 树里找最大的、看起来像参与者的数组
_FIND_PARTICIPANTS_JS = r"""
function looksLikeParticipant(item) {
    if (!item || typeof item !== 'object') return false;
    var code = item.code || item.studentCode || item.stuCode || item.userCode;
    // 至少有学号字段才算
    return !!code;
}

function collect(el, results) {
    if (el.__vue__) {
        var vm = el.__vue__;
        var data = vm.$data || {};
        for (var key in data) {
            var arr = data[key];
            if (Array.isArray(arr) && arr.length > 0 && looksLikeParticipant(arr[0])) {
                results.push({ key: key, data: arr, len: arr.length });
            }
        }
    }
    for (var i = 0; i < el.children.length; i++) {
        collect(el.children[i], results);
    }
}

var results = [];
collect(document.body, results);
if (results.length === 0) return null;
// 取最大的数组,避免拿到分页缓存里的子集
results.sort(function(a, b) { return b.len - a.len; });
return results[0].data;
"""


def get_participants_data(driver) -> Optional[List[Dict[str, Any]]]:
    """从当前页 Vue 实例里取最大的参与者数组。"""
    try:
        participants = driver.execute_script("return (function(){" + _FIND_PARTICIPANTS_JS + "})()")
        if participants and len(participants) > 0:
            first = participants[0] if isinstance(participants[0], dict) else {}
            keys = list(first.keys()) if first else []
            print(f"    当前页 {len(participants)} 条,字段示例: {keys[:8]}")
        return participants
    except Exception as e:
        print(f"    获取参与者数据失败: {e}")
        return None


# ============ 分页 ============

def get_participants_page_info(driver) -> Optional[Dict[str, int]]:
    """
    从'发放学分' tab 当前激活面板的 .el-pagination 里读取
    {total, pageSize, currentPage}。读不到就返回 None。
    """
    script = r"""
    // 取激活 tab 内的分页,避开报名/签到等其它 tab 残留的分页组件
    var tabPanes = document.querySelectorAll('.el-tab-pane');
    var paginations = [];
    tabPanes.forEach(function(pane) {
        if (getComputedStyle(pane).display === 'none') return;
        var ps = pane.querySelectorAll('.el-pagination');
        ps.forEach(function(p) { paginations.push(p); });
    });
    // 兜底:全文档第一个 .el-pagination
    if (paginations.length === 0) {
        var ps = document.querySelectorAll('.el-pagination');
        for (var i = 0; i < ps.length; i++) paginations.push(ps[i]);
    }
    if (paginations.length === 0) return null;

    var pag = paginations[0];
    // 从 .el-pagination__total 读 "共 N 条"
    var totalText = (pag.querySelector('.el-pagination__total') || {}).innerText || '';
    var m = totalText.replace(/[^0-9]/g, '');
    var total = m ? parseInt(m, 10) : null;

    // 当前页(.is-active)
    var activeLi = pag.querySelector('li.number.active') || pag.querySelector('li.active');
    var currentPage = activeLi ? parseInt(activeLi.innerText, 10) : 1;

    // 每页条数:从分页旁边的输入框读
    var sizeInput = pag.querySelector('.el-input__inner');
    var pageSize = null;
    if (sizeInput && sizeInput.value) pageSize = parseInt(sizeInput.value, 10);

    return { total: total, currentPage: currentPage, pageSize: pageSize };
    """
    try:
        info = driver.execute_script(script)
        if info and info.get("total"):
            return info
    except Exception as e:
        print(f"    读分页信息失败: {e}")
    return None


def go_to_next_participants_page(driver) -> bool:
    """点击当前激活面板里的 .btn-next。"""
    script = r"""
    var tabPanes = document.querySelectorAll('.el-tab-pane');
    var btn = null;
    tabPanes.forEach(function(pane) {
        if (getComputedStyle(pane).display === 'none') return;
        var b = pane.querySelector('.el-pagination .btn-next');
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
        result = driver.execute_script(script)
        if result == "ok":
            time.sleep(2)
            return True
        if result == "disabled":
            print("    .btn-next 已禁用,可能已经是最后一页")
        elif result == "no-btn":
            print("    未找到 .btn-next")
        return False
    except Exception as e:
        print(f"    翻页失败: {e}")
        return False


# ============ 签到/签退状态 ============

def check_sign_in_status(participants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """检测整批参与者里是否出现过签到/签退记录"""
    has_sign_in = False
    has_sign_out = False
    for p in participants:
        if not isinstance(p, dict):
            continue
        if p.get("signInTime") or p.get("sign_in_time") or p.get("inTime"):
            has_sign_in = True
        if p.get("signOutTime") or p.get("sign_out_time") or p.get("outTime"):
            has_sign_out = True
        if has_sign_in and has_sign_out:
            break
    return {"has_sign_in": has_sign_in, "has_sign_out": has_sign_out}


# ============ 主流程 ============

def _student_code_of(p: Dict[str, Any]) -> Optional[str]:
    """统一拿学号字段(用于去重)"""
    if not isinstance(p, dict):
        return None
    return str(p.get("code") or p.get("studentCode") or p.get("stuCode") or p.get("userCode") or "") or None


def crawl_activity_participants(driver, act_id: int) -> Optional[Dict[str, Any]]:
    """
    爬取单个活动全部参与者(逐页 + 去重)。
    返回:
        {"act_id": int, "participants": [...], "status": {has_sign_in, has_sign_out}}
        失败返回 None。
    """
    print(f"\n[*] 爬取活动 {act_id} 的参与者...")

    driver.get(ACTIVITY_DETAIL_URL_TEMPLATE.format(act_id))
    time.sleep(3)

    if not click_credit_tab(driver):
        return None

    # 请求一次大 page_size。即便平台不接受也无所谓,后面会以实际值为准翻页。
    print(f"    [*] 尝试设置每页 {settings.PARTICIPANT_PAGE_SIZE} 条")
    set_participant_page_size(driver, settings.PARTICIPANT_PAGE_SIZE)

    # 读首页
    first_page = get_participants_data(driver)
    if not first_page:
        print("    首页无数据(活动可能没有报名学生)")
        return {"act_id": act_id, "participants": [], "status": {"has_sign_in": False, "has_sign_out": False}}

    # 读 total
    info = get_participants_page_info(driver)
    total = info.get("total") if info else None
    real_page_size = len(first_page)
    if total is None:
        # 读不到 total,只能信首页数据
        print(f"    无法读取 total,仅返回首页 {real_page_size} 条")
        return {
            "act_id": act_id,
            "participants": first_page,
            "status": check_sign_in_status(first_page),
        }

    print(f"    total={total}, 首页实际 {real_page_size} 条")

    # 合并 + 去重
    all_participants: List[Dict[str, Any]] = []
    seen = set()

    def add(rows: List[Dict[str, Any]]) -> int:
        added = 0
        for r in rows:
            code = _student_code_of(r)
            if not code:
                continue
            if code in seen:
                continue
            seen.add(code)
            all_participants.append(r)
            added += 1
        return added

    add(first_page)

    # 如果首页就拿全了(没分页或 page_size 真的撑住了),直接收工
    if len(all_participants) >= total:
        print(f"    首页已覆盖全部 {total} 条,无需翻页")
        return {"act_id": act_id, "participants": all_participants, "status": check_sign_in_status(all_participants)}

    # 估算总页数,做翻页循环
    total_pages = (total + real_page_size - 1) // real_page_size if real_page_size else 1
    print(f"    需翻页: 每页 {real_page_size} 条 x {total_pages} 页")

    for page_idx in range(2, total_pages + 1):
        if not go_to_next_participants_page(driver):
            print(f"    第 {page_idx} 页翻页失败,中断")
            break

        # 等数据加载
        rows = None
        for _ in range(10):  # 最多 5 秒
            rows = get_participants_data(driver)
            if rows and len(rows) > 0 and _student_code_of(rows[0]) not in seen:
                break
            time.sleep(0.5)

        if not rows:
            print(f"    第 {page_idx} 页未拿到数据,中断")
            break

        added = add(rows)
        print(f"    第 {page_idx}/{total_pages} 页新增 {added} 条 (累计 {len(all_participants)}/{total})")

        if len(all_participants) >= total:
            break

    # 完整性检查
    if len(all_participants) < total:
        print(f"    [WARN] 抓取不完整: {len(all_participants)}/{total}")
    else:
        print(f"    完整抓取 {len(all_participants)} 条")

    return {
        "act_id": act_id,
        "participants": all_participants,
        "status": check_sign_in_status(all_participants),
    }


def crawl_participants_batch(driver, act_ids: List[int], stop_check=None, progress_callback=None) -> List[Dict[str, Any]]:
    """批量爬取多个活动"""
    total = len(act_ids)
    results = []
    success_count = 0
    fail_count = 0
    incomplete_count = 0

    print(f"\n{'='*60}")
    print(f"开始爬取 {total} 个活动的参与者信息")
    print(f"{'='*60}")

    for i, act_id in enumerate(act_ids, 1):
        if stop_check and stop_check():
            print("\n[停止] 收到停止信号,中断爬取")
            break

        print(f"\n[{i}/{total}] 活动 {act_id}")
        result = crawl_activity_participants(driver, act_id)

        if result:
            results.append(result)
            success_count += 1
            print(f"    [OK] 共 {len(result['participants'])} 条")
        else:
            fail_count += 1
            print(f"    [X] 失败")

        if progress_callback:
            progress_callback(i, total)

        if i % 5 == 0:
            print(f"\n进度: {i}/{total} ({i*100//total}%), 成功 {success_count}, 失败 {fail_count}")

        time.sleep(2)

    print(f"\n{'='*60}")
    print(f"爬取完成: 总计 {total}, 成功 {success_count}, 失败 {fail_count}")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    from app.crawlers.login import login

    driver = login()
    if driver:
        try:
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
