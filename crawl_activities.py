#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动数据爬虫 - 支持翻页
登录后爬取全部活动列表数据并保存到MySQL
"""

import time
import json
import pymysql
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from main import login

# ============ 配置 ============
ACTIVITY_URL = "https://2ketangpc.svtcc.edu.cn/communist/activityDown?oto=0"
PAGE_SIZE = 2000  # 每页条数
MAX_PAGES = None  # 最大爬取页数，None表示爬取全部

# MySQL数据库配置
DB_CONFIG = {
    'host': '10.5.80.8',
    'user': 'root',
    'password': '123456',
    'database': '2ketang',
    'charset': 'utf8mb4'
}
# ==============================


def get_page_info(driver):
    """获取分页信息"""
    try:
        script = """
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
        return driver.execute_script(script)
    except:
        return None


def get_current_page_data(driver, prev_first_id=None, max_wait=15):
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


def get_data_count(driver):
    """获取当前页面数据条数"""
    script = """
    function findActivityData(el) {
        if (el.__vue__) {
            var vm = el.__vue__;
            var data = vm.$data || {};
            if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                var item = data.data[0];
                if (item && item.actId && item.name) {
                    return data.data.length;
                }
            }
        }
        for (var i = 0; i < el.children.length; i++) {
            var result = findActivityData(el.children[i]);
            if (result) return result;
        }
        return 0;
    }
    return findActivityData(document.body);
    """
    return driver.execute_script(script)


def set_page_size(driver, size):
    """设置每页显示条数"""
    try:
        time.sleep(3)
        page_input = driver.find_element(By.CSS_SELECTOR, ".page-input input.el-input__inner")
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
        return True
    except Exception as e:
        print(f"    设置每页条数失败: {e}")
        return False


def click_next_page(driver):
    """点击下一页按钮"""
    try:
        # 等待加载遮罩消失
        for i in range(10):
            masks = driver.find_elements(By.CSS_SELECTOR, ".el-loading-mask")
            visible_masks = [m for m in masks if m.is_displayed()]
            if not visible_masks:
                break
            print(f"    等待加载遮罩消失... ({i+1}/10)")
            time.sleep(1)
        
        # 尝试多种方式找到下一页按钮
        next_btn = None
        
        # 方式1: CSS选择器 - el-pagination的btn-next
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, ".el-pagination .btn-next")
        except:
            pass
        
        # 方式2: 找包含el-icon-arrow-right的按钮
        if not next_btn:
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-next")
            except:
                pass
        
        # 方式3: JS查找
        if not next_btn:
            try:
                next_btn = driver.execute_script("""
                    return document.querySelector('.el-pagination button.btn-next') ||
                           document.querySelector('.el-pagination .el-icon-arrow-right').parentElement;
                """)
            except:
                pass
        
        if next_btn:
            driver.execute_script("arguments[0].click();", next_btn)
            print(f"    点击下一页按钮...")
            time.sleep(5)
            return True
        else:
            print(f"    找不到下一页按钮")
            return False
            
    except Exception as e:
        print(f"    点击下一页失败: {e}")
        return False


def init_database():
    """初始化数据库和表"""
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        charset=DB_CONFIG['charset']
    )
    cursor = conn.cursor()
    
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` DEFAULT CHARSET utf8mb4")
    cursor.execute(f"USE `{DB_CONFIG['database']}`")
    
    cursor.execute("DROP TABLE IF EXISTS activities")
    
    create_table_sql = """
    CREATE TABLE activities (
        act_id INT PRIMARY KEY COMMENT '活动ID',
        name VARCHAR(500) NOT NULL COMMENT '活动名称',
        class_id INT COMMENT '分类ID',
        class_name VARCHAR(100) COMMENT '分类名称',
        org_id INT COMMENT '组织ID',
        org_name VARCHAR(200) COMMENT '组织名称',
        admin_id INT COMMENT '管理员ID',
        admin_code VARCHAR(50) COMMENT '管理员代码',
        admin_name VARCHAR(100) COMMENT '管理员名称',
        creator_id INT COMMENT '创建者ID',
        hours DECIMAL(5,2) COMMENT '学时',
        start_time DATETIME COMMENT '开始时间',
        end_time DATETIME COMMENT '结束时间',
        enroll_end_time DATETIME COMMENT '报名截止时间',
        status TINYINT COMMENT '状态',
        apply_status TINYINT COMMENT '申请状态',
        status_all TINYINT COMMENT '总状态',
        oto TINYINT COMMENT '类型标识',
        edit_activity TINYINT COMMENT '是否可编辑',
        chenge_status TINYINT COMMENT '变更状态',
        finish_status VARCHAR(50) COMMENT '完成状态',
        finish_status2 VARCHAR(50) COMMENT '完成状态2',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        INDEX idx_name (name(100)),
        INDEX idx_class_id (class_id),
        INDEX idx_org_id (org_id),
        INDEX idx_start_time (start_time)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='第二课堂活动信息表'
    """
    cursor.execute(create_table_sql)
    print("[DB] 已重建activities表")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[DB] 数据库和表初始化完成")


def timestamp_to_datetime(ts):
    """时间戳转datetime"""
    if ts and isinstance(ts, (int, float)) and ts > 0:
        return datetime.fromtimestamp(ts / 1000)
    return None


def save_batch_to_mysql(activities):
    """批量保存活动数据到MySQL"""
    if not activities:
        return 0
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    insert_sql = """
    REPLACE INTO activities (
        act_id, name, class_id, class_name, org_id, org_name,
        admin_id, admin_code, admin_name, creator_id, hours,
        start_time, end_time, enroll_end_time,
        status, apply_status, status_all, oto, edit_activity,
        chenge_status, finish_status, finish_status2
    ) VALUES (
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s
    )
    """
    
    success_count = 0
    fail_count = 0
    
    for act in activities:
        try:
            if not act.get('actId'):
                fail_count += 1
                continue
            
            def to_int_or_none(val):
                if val == '' or val is None:
                    return None
                return val
            
            values = (
                act.get('actId'),
                act.get('name'),
                to_int_or_none(act.get('classId')),
                act.get('className'),
                to_int_or_none(act.get('orgId')),
                act.get('orgName'),
                to_int_or_none(act.get('adminId')),
                act.get('adminCode'),
                act.get('adminName'),
                to_int_or_none(act.get('creatorId')),
                act.get('hours'),
                timestamp_to_datetime(act.get('startTime')),
                timestamp_to_datetime(act.get('endTime')),
                timestamp_to_datetime(act.get('enrollEndTime')),
                to_int_or_none(act.get('status')),
                to_int_or_none(act.get('applyStatus')),
                to_int_or_none(act.get('statusAll')),
                to_int_or_none(act.get('oto')),
                to_int_or_none(act.get('editActivity')),
                to_int_or_none(act.get('chengeStatus')),
                act.get('finishStatus') if act.get('finishStatus') != '' else None,
                act.get('finishStatus2') if act.get('finishStatus2') != '' else None
            )
            cursor.execute(insert_sql, values)
            success_count += 1
        except Exception as e:
            fail_count += 1
            if fail_count <= 3:
                print(f"    写入失败: {act.get('actId')} - {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    if fail_count > 0:
        print(f"    本批次: 成功 {success_count}, 失败 {fail_count}")
    
    return success_count


def crawl_all_pages(driver):
    """爬取所有页面的活动数据"""
    print("\n[6] 访问活动列表页面...")
    driver.get(ACTIVITY_URL)
    time.sleep(3)
    
    page_info = get_page_info(driver)
    if page_info:
        total = page_info['total']
        print(f"[7] 总共 {total} 条活动数据")
    else:
        print("[7] 无法获取总数")
        total = 999999
    
    print(f"[8] 输入每页 {PAGE_SIZE} 条并按回车...")
    set_page_size(driver, PAGE_SIZE)
    
    print("    等待数据加载...")
    for i in range(20):
        time.sleep(1)
        data_count = get_data_count(driver)
        if data_count and data_count >= PAGE_SIZE * 0.9:
            print(f"    数据加载完成: {data_count} 条")
            break
        print(f"    加载中... ({i+1}/20) 当前: {data_count} 条")
    
    init_database()
    
    all_activities = []
    total_saved = 0
    page = 1
    max_pages = MAX_PAGES or (total // PAGE_SIZE + 1)
    prev_first_id = None
    
    print(f"\n[9] 开始爬取数据 (预计 {max_pages} 页)...")
    
    while page <= max_pages:
        time.sleep(2)
        
        if page == 1:
            activities = get_current_page_data(driver)
        else:
            activities = get_current_page_data(driver, prev_first_id, max_wait=20)
        
        if not activities or len(activities) == 0:
            print(f"    第 {page} 页无数据，停止爬取")
            break
        
        current_first_id = activities[0].get('actId') if activities else None
        
        saved = save_batch_to_mysql(activities)
        total_saved += saved
        
        existing_ids = {a.get('actId') for a in all_activities}
        new_activities = [a for a in activities if a.get('actId') not in existing_ids]
        all_activities.extend(new_activities)
        
        print(f"    第 {page}/{max_pages} 页: 获取 {len(activities)} 条, 新增 {len(new_activities)} 条, 累计 {len(all_activities)} 条")
        
        prev_first_id = current_first_id
        
        if len(activities) < PAGE_SIZE:
            print(f"    当前页只有 {len(activities)} 条，已到最后一页")
            break
        
        page += 1
        if page <= max_pages:
            if not click_next_page(driver):
                print("    无法翻页，停止爬取")
                break
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM activities")
        db_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
    except:
        db_count = "未知"
    
    print(f"\n[10] 爬取完成!")
    print(f"    内存中去重后: {len(all_activities)} 条唯一记录")
    print(f"    数据库实际记录: {db_count} 条")
    
    with open("activities_data.json", "w", encoding="utf-8") as f:
        json.dump(all_activities, f, ensure_ascii=False, indent=2, default=str)
    print(f"    数据已保存到 activities_data.json")
    
    return all_activities


def main():
    print("=" * 60)
    print("第二课堂活动数据爬虫 - 支持翻页")
    print("=" * 60)
    
    driver = login()
    
    if not driver:
        print("登录失败，无法继续")
        return
    
    try:
        crawl_all_pages(driver)
    except KeyboardInterrupt:
        print("\n\n用户中断...")
    except Exception as e:
        print(f"\n爬取异常: {e}")
    finally:
        print("\n等待3秒后关闭浏览器...")
        time.sleep(3)
        driver.quit()


if __name__ == "__main__":
    main()
