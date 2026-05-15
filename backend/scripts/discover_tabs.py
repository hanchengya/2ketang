#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性探测脚本: 登录第二课堂, 列出活动页面的所有 tab。

用法 (在 backend 容器里):
    python scripts/discover_tabs.py
"""
import sys
import time

sys.path.insert(0, "/app")  # 容器里代码挂在 /app

from app.crawlers.login import login
from selenium.webdriver.common.by import By

ACTIVITY_LIST_URL = "https://2ketangpc.svtcc.edu.cn/communist/activityDown?oto=0"


def main():
    print("[*] 启动浏览器并登录...")
    driver = login()
    if not driver:
        print("登录失败")
        return 1

    try:
        print(f"[*] 访问 {ACTIVITY_LIST_URL}")
        driver.get(ACTIVITY_LIST_URL)
        time.sleep(6)  # 等 Vue 渲染

        print("\n========== 所有 .el-tabs__item ==========")
        tabs = driver.find_elements(By.CSS_SELECTOR, ".el-tabs__item")
        if not tabs:
            print("  未找到 .el-tabs__item")
        for t in tabs:
            tid = t.get_attribute("id") or ""
            text = (t.text or "").strip()
            visible = t.is_displayed()
            cls = t.get_attribute("class") or ""
            print(f"  id={tid:<10} text={text!r:<14} visible={visible} class={cls}")

        print("\n========== id^=tab- 的元素 (备用) ==========")
        anchors = driver.find_elements(By.XPATH, '//*[starts-with(@id, "tab-")]')
        for a in anchors:
            tid = a.get_attribute("id") or ""
            text = (a.text or "").strip()
            print(f"  id={tid:<10} text={text!r}")

        # 尝试点击每个 tab,看是否切换并取到不同的总数
        print("\n========== 点击每个 tab 后的 .el-pagination__total ==========")
        for t in tabs:
            tid = t.get_attribute("id") or ""
            label = (t.text or "").strip()
            try:
                driver.execute_script("arguments[0].click();", t)
                time.sleep(3)
                # 读取总数文本
                totals = driver.find_elements(By.CSS_SELECTOR, ".el-pagination__total")
                total_text = totals[0].text if totals else "(无)"
                # 也读 url hash 看看
                url = driver.execute_script("return location.href")
                print(f"  {tid} ({label}): total={total_text!r}  url={url}")
            except Exception as e:
                print(f"  {tid} ({label}): 点击失败 {e}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
