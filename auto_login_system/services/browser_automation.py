"""
浏览器自动化组件
Browser Automation Component
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from typing import List, Optional
from PIL import Image
import io
import base64
import time

from ..models.data_models import Point, UIElements
from ..utils.logger import logger
from ..utils.config import LoginConfig


class BrowserAutomation:
    """浏览器自动化类，使用Selenium WebDriver控制浏览器"""
    
    def __init__(self, config: LoginConfig):
        """初始化浏览器自动化
        
        Args:
            config: 登录配置
        """
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.ui_elements = UIElements()
        self.wait_timeout = 10
    
    def _setup_driver(self) -> webdriver.Chrome:
        """设置Chrome WebDriver"""
        try:
            chrome_options = Options()
            
            # 基本配置
            if self.config.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument(f'--window-size={self.config.browser_width},{self.config.browser_height}')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            
            # 用户代理
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 禁用图片加载以提高速度（可选）
            # prefs = {"profile.managed_default_content_settings.images": 2}
            # chrome_options.add_experimental_option("prefs", prefs)
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(5)
            
            logger.info("Chrome WebDriver初始化成功")
            return driver
            
        except Exception as e:
            logger.error(f"WebDriver初始化失败: {e}")
            raise WebDriverException(f"WebDriver初始化失败: {e}")
    
    def open_login_page(self) -> None:
        """打开登录页面"""
        try:
            if self.driver is None:
                self.driver = self._setup_driver()
            
            logger.info(f"打开登录页面: {self.config.login_url}")
            self.driver.get(self.config.login_url)
            
            # 等待页面加载
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("登录页面加载完成")
            
        except TimeoutException:
            logger.error("登录页面加载超时")
            raise TimeoutException("登录页面加载超时")
        except Exception as e:
            logger.error(f"打开登录页面失败: {e}")
            raise WebDriverException(f"打开登录页面失败: {e}")
    
    def input_credentials(self, username: str, password: str) -> None:
        """输入用户名和密码
        
        Args:
            username: 用户名
            password: 密码
        """
        try:
            logger.info("开始输入登录凭据")
            
            # 等待并输入用户名
            username_element = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.element_to_be_clickable((By.XPATH, self.ui_elements.username_input))
            )
            username_element.clear()
            username_element.send_keys(username)
            logger.info("用户名输入完成")
            
            # 等待并输入密码
            password_element = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.element_to_be_clickable((By.XPATH, self.ui_elements.password_input))
            )
            password_element.clear()
            password_element.send_keys(password)
            logger.info("密码输入完成")
            
            # 短暂等待，模拟人类操作
            time.sleep(0.5)
            
        except TimeoutException:
            logger.error("输入凭据超时：找不到用户名或密码输入框")
            raise TimeoutException("找不到用户名或密码输入框")
        except Exception as e:
            logger.error(f"输入凭据失败: {e}")
            raise WebDriverException(f"输入凭据失败: {e}")
    
    def get_slider_image(self) -> Optional[Image.Image]:
        """获取滑块验证码图像
        
        Returns:
            Image.Image: 滑块验证码图像，如果获取失败返回None
        """
        try:
            logger.info("获取滑块验证码图像")
            
            # 等待滑块验证码出现
            canvas_element = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.XPATH, self.ui_elements.slider_canvas))
            )
            
            # 获取canvas元素的截图
            canvas_screenshot = canvas_element.screenshot_as_png
            
            # 转换为PIL图像
            image = Image.open(io.BytesIO(canvas_screenshot))
            
            logger.info(f"滑块图像获取成功: 尺寸={image.size}")
            return image
            
        except TimeoutException:
            logger.error("获取滑块图像超时：找不到滑块canvas元素")
            return None
        except Exception as e:
            logger.error(f"获取滑块图像失败: {e}")
            return None
    
    def get_gap_position_from_js(self) -> Optional[int]:
        """通过JS逆向直接获取缺口位置
        
        从Vue组件的block_x属性获取缺口X坐标
        
        Returns:
            int: 缺口位置（像素），如果获取失败返回None
        """
        try:
            script = """
            var el = document.getElementById('slideVerify');
            if (el && el.__vue__) {
                return el.__vue__.block_x;
            }
            return null;
            """
            result = self.driver.execute_script(script)
            if result is not None:
                logger.info(f"JS逆向获取缺口位置: {result}px")
            return result
        except Exception as e:
            logger.warning(f"JS逆向获取缺口位置失败: {e}")
            return None
    
    def get_slide_distance(self, offset: int = 12) -> Optional[int]:
        """获取滑动距离
        
        优先使用JS逆向方式获取缺口位置，加上校准偏移值
        
        Args:
            offset: 校准偏移值（默认+15像素）
            
        Returns:
            int: 滑动距离（像素），如果获取失败返回None
        """
        gap_x = self.get_gap_position_from_js()
        if gap_x is not None:
            slide_distance = gap_x + offset
            logger.info(f"滑动距离: {slide_distance}px (缺口{gap_x}px + 偏移{offset}px)")
            return slide_distance
        return None
    
    def drag_slider(self, track_points: List[Point]) -> bool:
        """执行滑块拖拽操作
        
        Args:
            track_points: 滑动轨迹点列表
            
        Returns:
            bool: 拖拽是否成功
        """
        try:
            if not track_points:
                logger.warning("轨迹点列表为空")
                return False
            
            logger.info(f"开始执行滑块拖拽: {len(track_points)}个轨迹点")
            
            # 找到滑块按钮
            slider_button = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.element_to_be_clickable((By.XPATH, self.ui_elements.slider_button))
            )
            
            # 创建动作链
            actions = ActionChains(self.driver)
            
            # 点击并按住滑块
            actions.click_and_hold(slider_button)
            
            # 按照轨迹移动
            for i, point in enumerate(track_points):
                if i == 0:
                    continue  # 跳过起始点
                
                # 计算相对移动距离
                prev_point = track_points[i - 1]
                dx = point.x - prev_point.x
                dy = point.y - prev_point.y
                
                # 移动鼠标
                actions.move_by_offset(dx, dy)
                
                # 模拟时间间隔
                if i < len(track_points) - 1:
                    actions.pause(0.01)  # 10ms间隔
            
            # 释放鼠标
            actions.release()
            
            # 执行动作
            actions.perform()
            
            logger.info("滑块拖拽执行完成")
            
            # 等待验证结果
            time.sleep(1)
            
            return True
            
        except TimeoutException:
            logger.error("滑块拖拽超时：找不到滑块按钮")
            return False
        except Exception as e:
            logger.error(f"滑块拖拽失败: {e}")
            return False
    
    def wait_for_login_success(self, timeout: int = 10) -> bool:
        """等待登录成功
        
        Args:
            timeout: 等待超时时间（秒）
            
        Returns:
            bool: 是否登录成功
        """
        try:
            logger.info(f"等待登录成功，超时时间: {timeout}秒")
            
            # 等待页面跳转或出现成功标识
            # 这里可以根据具体网站的登录成功标识进行调整
            
            # 方法1: 检查URL变化
            original_url = self.driver.current_url
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                current_url = self.driver.current_url
                if current_url != original_url and 'login' not in current_url.lower():
                    logger.info(f"检测到页面跳转: {original_url} -> {current_url}")
                    return True
                
                # 方法2: 检查是否出现用户信息或主页元素
                try:
                    # 查找可能的成功标识元素
                    success_indicators = [
                        "//div[contains(@class, 'user')]",
                        "//div[contains(@class, 'welcome')]",
                        "//div[contains(@class, 'dashboard')]",
                        "//a[contains(@href, 'logout')]",
                        "//span[contains(text(), '欢迎')]"
                    ]
                    
                    for indicator in success_indicators:
                        try:
                            element = self.driver.find_element(By.XPATH, indicator)
                            if element.is_displayed():
                                logger.info(f"找到登录成功标识: {indicator}")
                                return True
                        except NoSuchElementException:
                            continue
                
                except Exception:
                    pass
                
                time.sleep(0.5)
            
            logger.warning("等待登录成功超时")
            return False
            
        except Exception as e:
            logger.error(f"等待登录成功失败: {e}")
            return False
    
    def get_page_source(self) -> str:
        """获取当前页面源码"""
        try:
            if self.driver:
                return self.driver.page_source
            return ""
        except Exception as e:
            logger.error(f"获取页面源码失败: {e}")
            return ""
    
    def take_screenshot(self, filename: Optional[str] = None) -> Optional[str]:
        """截取当前页面截图
        
        Args:
            filename: 保存文件名，如果为None则返回base64数据
            
        Returns:
            str: 截图的base64数据或文件路径
        """
        try:
            if not self.driver:
                return None
            
            if filename:
                screenshot_path = f"screenshots/{filename}"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"截图已保存: {screenshot_path}")
                return screenshot_path
            else:
                screenshot_data = self.driver.get_screenshot_as_base64()
                return screenshot_data
                
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def close(self) -> None:
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()