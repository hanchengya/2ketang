#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析活动页面数据结构
"""

import time
import json
from selenium.webdriver.common.by import By
from main import login

ACTIVITY_URL = "https://2ketangpc.svtcc.edu.cn/communist/activityDown?oto=0"

def analyze_page(driver):
    """分析页面数据结构"""
    print("\n[1] 访问活动页面...")
    driver.get(ACTIVITY_URL)
    time.sleep(5)
    
    print(f"[2] 当前页面: {driver.current_url}")
    print(f"[3] 页面标题: {driver.title}")
    
    # 获取页面总数信息
    print("\n[4] 获取分页信息...")
    page_info_script = """
    function findPageInfo(el) {
        if (el.__vue__) {
            var vm = el.__vue__;
            var data = vm.$data || {};
            if (data.total !== undefined) {
                return {total: data.total, pageSize: data.pageSize || 10, currentPage: data.currentPage || 1};
            }
        }
        for (var i = 0; i < el.children.length; i++) {
            var result = findPageInfo(el.children[i]);
            if (result) return result;
        }
        return null;
    }
    return findPageInfo(document.body);
    """
    page_info = driver.execute_script(page_info_script)
    print(f"    分页信息: {page_info}")
    
    # 获取数据结构
    print("\n[5] 分析数据结构...")
    data_script = """
    function findAllData(el, results) {
        results = results || [];
        if (el.__vue__) {
            var vm = el.__vue__;
            var data = vm.$data || {};
            for (var key in data) {
                if (Array.isArray(data[key]) && data[key].length > 0) {
                    var item = data[key][0];
                    // 只获取简单对象，避免循环引用
                    if (item && typeof item === 'object' && !Array.isArray(item)) {
                        try {
                            var fields = Object.keys(item);
                            // 创建简化的示例数据
                            var sample = {};
                            for (var f of fields) {
                                var val = item[f];
                                if (val === null || val === undefined) {
                                    sample[f] = null;
                                } else if (typeof val === 'object') {
                                    sample[f] = '[object]';
                                } else {
                                    sample[f] = val;
                                }
                            }
                            results.push({
                                key: key, 
                                length: data[key].length,
                                sample: sample,
                                fields: fields
                            });
                        } catch(e) {}
                    }
                }
            }
        }
        for (var i = 0; i < el.children.length; i++) {
            findAllData(el.children[i], results);
        }
        return results;
    }
    return findAllData(document.body, []);
    """
    all_data = driver.execute_script(data_script)
    
    print(f"    找到 {len(all_data)} 个数据数组:")
    for item in all_data:
        print(f"\n    数组名: {item['key']}, 长度: {item['length']}")
        print(f"    字段: {item['fields']}")
        print(f"    示例数据: {json.dumps(item['sample'], ensure_ascii=False, indent=6)}")
    
    # 保存分析结果
    with open("activity_structure.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print("\n[6] 数据结构已保存到 activity_structure.json")
    
    return all_data


def main():
    print("=" * 60)
    print("分析活动页面数据结构")
    print("=" * 60)
    
    driver = login()
    
    if not driver:
        print("登录失败")
        return
    
    try:
        analyze_page(driver)
    finally:
        print("\n按回车键关闭浏览器...")
        input()
        driver.quit()


if __name__ == "__main__":
    main()
