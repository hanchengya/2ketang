#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生数据爬虫 - 支持翻页
登录后爬取全部学生列表数据并保存到MySQL
"""

import time
import json
import pymysql
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from main import login

# ============ 配置 ============
STUDENT_LIST_URL = "https://2ketangpc.svtcc.edu.cn/student/list?type=4"
PAGE_SIZE = 2000  # 每页条数（网站最大支持2000条）
MAX_PAGES = None  # 最大爬取页数，None表示爬取全部（测试时设为5页）

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
    """获取分页信息：总条数和总页数"""
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


def get_current_page_data(driver, prev_first_id=None, max_wait=15):
    """从Vue组件获取当前页的学生数据，确保数据已更新"""
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
    var all = findAllStudentData(document.body, []);
    // 返回最大的数组
    if (all.length === 0) return null;
    var max = all[0];
    for (var i = 1; i < all.length; i++) {
        if (all[i].len > max.len) max = all[i];
    }
    return max.data;
    """
    
    # 如果有上一页的第一条ID，等待数据变化
    if prev_first_id:
        print(f"    等待数据更新 (上一页首条ID: {prev_first_id})...")
        for i in range(max_wait):
            data = driver.execute_script(script)
            if data and len(data) > 0:
                current_first_id = data[0].get('id')
                if current_first_id != prev_first_id:
                    print(f"    数据已更新 (新首条ID: {current_first_id}, 共{len(data)}条)")
                    return data
                else:
                    print(f"    等待中... ({i+1}/{max_wait}) 首条ID仍为 {current_first_id}, 当前{len(data)}条")
            time.sleep(1)
        print(f"    警告: 等待{max_wait}秒后数据仍未更新，强制读取")
    
    return driver.execute_script(script)


def set_page_size(driver, size):
    """设置每页显示条数：输入数量 → 按回车键触发加载"""
    from selenium.webdriver.common.keys import Keys
    
    try:
        # 等待页面完全加载
        time.sleep(3)
        
        # 找到每页条数输入框并输入数量
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
        
        # 按回车键触发加载
        page_input.send_keys(Keys.ENTER)
        print(f"    按回车键触发加载...")
        return True
            
    except Exception as e:
        print(f"    设置每页条数失败: {e}")
        return False


def get_data_count(driver):
    """获取当前页面加载的数据条数（返回最大的学生数据数组长度）"""
    script = """
    function findMaxStudentCount(el, maxCount) {
        maxCount = maxCount || 0;
        if (el.__vue__) {
            var vm = el.__vue__;
            var data = vm.$data || {};
            for (var key in data) {
                if (Array.isArray(data[key]) && data[key].length > 0) {
                    var item = data[key][0];
                    if (item && item.code && item.name) {
                        if (data[key].length > maxCount) {
                            maxCount = data[key].length;
                        }
                    }
                }
            }
        }
        for (var i = 0; i < el.children.length; i++) {
            var childMax = findMaxStudentCount(el.children[i], maxCount);
            if (childMax > maxCount) maxCount = childMax;
        }
        return maxCount;
    }
    return findMaxStudentCount(document.body, 0);
    """
    return driver.execute_script(script)


def click_next_page(driver):
    """点击下一页按钮"""
    # 下一页按钮XPath（不带/i，点击button本身）
    NEXT_BTN_XPATH = '//*[@id="app"]/div/div/div[1]/section/div[6]/div[2]/div[2]/button[2]'
    
    try:
        # 等待加载遮罩层消失
        for i in range(10):
            masks = driver.find_elements(By.CSS_SELECTOR, ".el-loading-mask")
            visible_masks = [m for m in masks if m.is_displayed()]
            if not visible_masks:
                break
            print(f"    等待加载遮罩消失... ({i+1}/10)")
            time.sleep(1)
        
        # 使用JS点击，避免被遮挡
        next_btn = driver.find_element(By.XPATH, NEXT_BTN_XPATH)
        driver.execute_script("arguments[0].click();", next_btn)
        print(f"    点击下一页按钮...")
        time.sleep(5)  # 等待数据加载
        return True
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
    
    # 先删除旧表（因为要修改主键）
    cursor.execute("DROP TABLE IF EXISTS students")
    
    create_table_sql = """
    CREATE TABLE students (
        code VARCHAR(20) PRIMARY KEY COMMENT '学号',
        id INT COMMENT '学生ID',
        name VARCHAR(50) NOT NULL COMMENT '姓名',
        gender TINYINT COMMENT '性别: 1=男, 2=女',
        ethnic VARCHAR(20) COMMENT '民族',
        ethnic_id INT COMMENT '民族ID',
        politics TINYINT COMMENT '政治面貌: 0=群众, 1=团员, 2=党员',
        mobile VARCHAR(20) COMMENT '手机号',
        identity TINYINT COMMENT '身份类型',
        campus_id INT COMMENT '校区ID',
        campus_name VARCHAR(100) COMMENT '校区名称',
        college_id INT COMMENT '院系ID',
        college_name VARCHAR(100) COMMENT '院系名称',
        major_id INT COMMENT '专业ID',
        major_name VARCHAR(100) COMMENT '专业名称',
        class_id INT COMMENT '班级ID',
        class_name VARCHAR(50) COMMENT '班级名称',
        grade INT COMMENT '年级ID',
        grade_name VARCHAR(20) COMMENT '年级名称',
        length_name VARCHAR(20) COMMENT '学制',
        credit DECIMAL(10,2) COMMENT '学分',
        sum_score DECIMAL(10,2) COMMENT '总分',
        user_class_pass VARCHAR(10) COMMENT '是否通过',
        status TINYINT COMMENT '状态: 3=正常',
        leave_total_num INT DEFAULT 0 COMMENT '请假总次数',
        leave_success_num INT DEFAULT 0 COMMENT '请假成功次数',
        leave_fail_num INT DEFAULT 0 COMMENT '请假失败次数',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        INDEX idx_id (id),
        INDEX idx_name (name),
        INDEX idx_class_id (class_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='第二课堂学生信息表'
    """
    cursor.execute(create_table_sql)
    print("[DB] 已重建students表")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[DB] 数据库和表初始化完成")


def save_batch_to_mysql(students):
    """批量保存学生数据到MySQL"""
    if not students:
        return 0
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    insert_sql = """
    REPLACE INTO students (
        code, id, name, gender, ethnic, ethnic_id, politics, mobile, identity,
        campus_id, campus_name, college_id, college_name, major_id, major_name,
        class_id, class_name, grade, grade_name, length_name,
        credit, sum_score, user_class_pass, status,
        leave_total_num, leave_success_num, leave_fail_num
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s
    )
    """
    
    success_count = 0
    fail_count = 0
    for student in students:
        try:
            # 跳过没有code的记录
            if not student.get('code'):
                fail_count += 1
                continue
                
            # 处理空字符串转None（避免INT字段插入空字符串报错）
            def to_int_or_none(val):
                if val == '' or val is None:
                    return None
                return val
            
            values = (
                student.get('code'),
                student.get('id'),
                student.get('name'),
                to_int_or_none(student.get('gender')),
                student.get('ethnic') if student.get('ethnic') != '' else None,
                to_int_or_none(student.get('ethnicId')),
                to_int_or_none(student.get('politics')),
                student.get('mobile'),
                to_int_or_none(student.get('identity')),
                to_int_or_none(student.get('campusId')),
                student.get('campusName'),
                to_int_or_none(student.get('collegeId')),
                student.get('collegeName'),
                to_int_or_none(student.get('majorId')),
                student.get('majorName'),
                to_int_or_none(student.get('classId')),
                student.get('className'),
                to_int_or_none(student.get('grade')),
                student.get('gradeName'),
                student.get('lengthName'),
                student.get('credit'),
                student.get('sumScore'),
                student.get('userClassPass'),
                to_int_or_none(student.get('status')),
                student.get('leaveTotalNum', 0) or 0,
                student.get('leaveSuccessNum', 0) or 0,
                student.get('leaveFailNum', 0) or 0
            )
            cursor.execute(insert_sql, values)
            success_count += 1
        except Exception as e:
            fail_count += 1
            # 只打印前几个错误
            if fail_count <= 3:
                print(f"    写入失败: {student.get('code')} - {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    if fail_count > 0:
        print(f"    本批次: 成功 {success_count}, 失败 {fail_count}")
    
    return success_count



def crawl_all_pages(driver):
    """爬取所有页面的学生数据"""
    print("\n[6] 访问学生列表页面...")
    driver.get(STUDENT_LIST_URL)
    time.sleep(3)
    
    # 获取分页信息
    page_info = get_page_info(driver)
    if page_info:
        total = page_info['total']
        print(f"[7] 总共 {total} 条学生数据")
    else:
        print("[7] 无法获取总数，将持续爬取直到没有数据")
        total = 999999
    
    # 输入每页2000条并按回车触发加载
    print(f"[8] 输入每页 {PAGE_SIZE} 条并按回车...")
    set_page_size(driver, PAGE_SIZE)
    
    # 等待第一页数据加载完成
    print("    等待第一页数据加载...")
    for i in range(20):
        time.sleep(1)
        data_count = get_data_count(driver)
        if data_count and data_count >= PAGE_SIZE * 0.9:
            print(f"    第一页数据加载完成: {data_count} 条")
            break
        print(f"    加载中... ({i+1}/20) 当前: {data_count} 条")
    
    # 初始化数据库
    init_database()
    
    all_students = []
    total_saved = 0
    page = 1
    max_pages = MAX_PAGES or (total // PAGE_SIZE + 1)
    prev_first_id = None  # 上一页第一条数据的ID，用于验证翻页成功
    
    print(f"\n[9] 开始爬取数据 (预计 {max_pages} 页)...")
    
    while page <= max_pages:
        # 等待数据加载
        time.sleep(2)
        
        # 获取当前页数据
        if page == 1:
            # 第一页直接读取
            students = get_current_page_data(driver)
        else:
            # 后续页需要验证数据已更新（首条ID变化）
            students = get_current_page_data(driver, prev_first_id, max_wait=20)
        
        # 验证数据
        if not students or len(students) == 0:
            print(f"    第 {page} 页无数据，停止爬取")
            break
        
        # 检查数据量
        current_first_id = students[0].get('id') if students else None
        
        # 前15页必须是完整的2000条
        if page <= 15 and len(students) < PAGE_SIZE:
            print(f"    警告: 第 {page} 页数据不完整 ({len(students)}/{PAGE_SIZE})")
        
        # 保存到数据库
        saved = save_batch_to_mysql(students)
        total_saved += saved
        
        # 去重后添加到列表（用code学号去重）
        existing_codes = {s.get('code') for s in all_students}
        new_students = [s for s in students if s.get('code') not in existing_codes]
        all_students.extend(new_students)
        
        print(f"    第 {page}/{max_pages} 页: 获取 {len(students)} 条, 新增 {len(new_students)} 条, 累计 {len(all_students)} 条, 首条ID: {current_first_id}")
        
        # 记录当前页第一条数据的ID
        prev_first_id = current_first_id
        
        # 检查是否是最后一页（少于PAGE_SIZE条也继续写入，只是不再翻页）
        if len(students) < PAGE_SIZE:
            print(f"    当前页只有 {len(students)} 条，已到最后一页，数据已写入")
            break
        
        # 点击下一页按钮跳转到下一页
        page += 1
        if page <= max_pages:
            if not click_next_page(driver):
                print("    无法翻页，停止爬取")
                break
    
    # 查询数据库中的实际记录数
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        db_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
    except:
        db_count = "未知"
    
    print(f"\n[10] 爬取完成!")
    print(f"    内存中去重后: {len(all_students)} 条唯一记录")
    print(f"    数据库实际记录: {db_count} 条")
    
    # 保存到JSON文件
    with open("students_data.json", "w", encoding="utf-8") as f:
        json.dump(all_students, f, ensure_ascii=False, indent=2)
    print(f"    数据已保存到 students_data.json")
    
    return all_students


def main():
    """主函数"""
    print("=" * 60)
    print("第二课堂学生数据爬虫 - 支持翻页")
    print("=" * 60)
    
    # 登录
    driver = login()
    
    if not driver:
        print("登录失败，无法继续")
        return
    
    try:
        # 爬取所有页面
        students = crawl_all_pages(driver)
        
        if not students:
            print("\n未能获取学生数据")
        
    except KeyboardInterrupt:
        print("\n\n用户中断，正在保存已爬取的数据...")
    except Exception as e:
        print(f"\n爬取异常: {e}")
    finally:
        print("\n等待3秒后关闭浏览器...")
        time.sleep(3)
        driver.quit()


if __name__ == "__main__":
    main()
