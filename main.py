#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二课堂自动登录系统
简单版 - 直接运行即可登录
"""

import sys
import time
import random
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

# ============ 配置区域 ============
USERNAME = "2004"
PASSWORD = "yxsh2004,,."
LOGIN_URL = "https://2ketangpc.svtcc.edu.cn/login"
SLIDE_OFFSET = 12  # 滑动偏移校准值
# =================================


def get_gap_position(driver) -> int:
    """通过JS获取缺口位置"""
    script = """
    var el = document.getElementById('slideVerify');
    if (el && el.__vue__) {
        return el.__vue__.block_x;
    }
    return null;
    """
    return driver.execute_script(script)


def generate_track(distance: int):
    """生成人类化滑动轨迹"""
    track = []
    current = 0
    mid = distance * 0.7
    t = 0.2
    v = 0
    
    while current < distance:
        if current < mid:
            a = 2
        else:
            a = -3
        v0 = v
        v = v0 + a * t
        move = v0 * t + 0.5 * a * t * t
        current += move
        track.append(round(move))
    
    return track


def login():
    """执行登录"""
    print("=" * 50)
    print("第二课堂自动登录系统")
    print("=" * 50)
    
    # 初始化浏览器
    options = Options()
    options.add_argument('--window-size=1366,768')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 1. 打开登录页面
        print("\n[1] 打开登录页面...")
        driver.get(LOGIN_URL)
        time.sleep(3)
        
        # 2. 输入账号密码
        print("[2] 输入账号密码...")
        username_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@class="login-input user"][1]'))
        )
        username_input.clear()
        username_input.send_keys(USERNAME)
        
        password_input = driver.find_element(By.XPATH, '//div[@class="val pwd-after"]//input')
        password_input.clear()
        password_input.send_keys(PASSWORD)
        
        # 3. 点击登录
        print("[3] 点击登录按钮...")
        login_btn = driver.find_element(By.XPATH, '//button[@id="login"]')
        login_btn.click()
        time.sleep(2)
        
        # 4. 处理滑块验证码
        print("[4] 处理滑块验证码...")
        
        for attempt in range(5):
            try:
                # 检查验证码对话框
                dialog = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "el-dialog__wrapper"))
                )
                if not dialog.is_displayed():
                    break
                
                print(f"    尝试 {attempt + 1}/5")
                time.sleep(1)
                
                # 获取缺口位置
                gap_x = get_gap_position(driver)
                if gap_x is None:
                    print("    无法获取缺口位置")
                    continue
                
                # 计算滑动距离
                slide_distance = gap_x + SLIDE_OFFSET
                print(f"    缺口位置: {gap_x}px, 滑动距离: {slide_distance}px")
                
                # 生成轨迹
                track = generate_track(slide_distance)
                
                # 执行滑动 - 快速直接滑动
                slider = driver.find_element(By.CLASS_NAME, "slide-verify-slider-mask-item")
                actions = ActionChains(driver)
                actions.click_and_hold(slider).perform()
                time.sleep(0.05)
                
                # 快速滑动：分3步完成
                step1 = int(slide_distance * 0.7)
                step2 = int(slide_distance * 0.2)
                step3 = slide_distance - step1 - step2
                
                actions.move_by_offset(step1, 0).perform()
                time.sleep(0.01)
                actions.move_by_offset(step2, 0).perform()
                time.sleep(0.01)
                actions.move_by_offset(step3, random.randint(-2, 2)).perform()
                
                actions.release().perform()
                time.sleep(2)
                
                # 检查是否成功
                try:
                    current_url = driver.current_url
                    if 'login' not in current_url.lower():
                        print(f"\n[5] 登录成功! 当前页面: {current_url}")
                        return driver  # 返回driver供后续使用
                except:
                    print("\n[5] 登录成功!")
                    return driver
                
                # 刷新验证码
                try:
                    refresh = driver.find_element(By.CLASS_NAME, "slide-verify-refresh-icon")
                    refresh.click()
                    time.sleep(1)
                except:
                    pass
                    
            except Exception as e:
                try:
                    current_url = driver.current_url
                    if 'login' not in current_url.lower():
                        print(f"\n[5] 登录成功! 当前页面: {current_url}")
                        return driver
                except:
                    print("\n[5] 登录成功!")
                    return driver
                print(f"    异常: {e}")
                break
        
        # 最终检查
        if 'login' not in driver.current_url.lower():
            print(f"\n[5] 登录成功! 当前页面: {driver.current_url}")
            return driver
        else:
            print("\n[5] 登录失败")
            driver.quit()
            return None
            
    except Exception as e:
        print(f"\n登录异常: {e}")
        driver.quit()
        return None


if __name__ == "__main__":
    driver = login()
    if driver:
        print("\n浏览器保持打开状态，按回车键关闭...")
        input()
        driver.quit()
