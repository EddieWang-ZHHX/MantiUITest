"""登录页面对象 - 包含身份选择功能"""
from pages.base_page import BasePage
from playwright.sync_api import Page
from utils.logger import logger
from typing import Optional, List


class LoginPage(BasePage):
    """
    登录页面
    
    功能：
    - 用户登录
    - 身份选择（登录后的弹窗/对话框）
    
    URL: /dataapp/login
    """
    
    # ===== 元素定位器 =====
    # 登录元素
    USERNAME_INPUT = "input[placeholder*='用户名'], input[placeholder*='户名']"
    PASSWORD_INPUT = "input[placeholder*='密码']"
    VERIFY_CODE_INPUT = "input[placeholder*='验证码']"
    VERIFY_CODE_IMAGE = "img[src*='code'], img:nth-of-type(2)"
    LOGIN_BUTTON = "button:has-text('登录'), input[type='submit']"
    FORGOT_PASSWORD_BUTTON = "button:has-text('忘记密码')"
    ERROR_MESSAGE = ".error-message, .msg-error, .tips-error"
    
    # 身份选择元素（弹窗/对话框）
    IDENTITY_DIALOG_TITLE = "text=您有多身份，请选择"
    IDENTITY_BUTTON = "button:has-text('{identity}'), div:has-text('{identity}')"
    
    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url)
    
    def open_login(self) -> "LoginPage":
        """打开登录页面"""
        return self.open("/login")
    
    def login(self, username: str, password: str, verify_code: str = "2222", 
              identity: Optional[str] = None) -> "LoginPage":
        """
        执行登录（包含身份选择）
        
        Args:
            username: 用户名
            password: 密码
            verify_code: 验证码（默认 2222）
            identity: 身份名称（可选，不传则选择第一个）
        """
        logger.info(f"登录：用户={username}")
        
        # 清空并填写表单
        self.page.locator("input[placeholder*='用户名']").fill("")
        self.page.locator("input[placeholder*='用户名']").fill(username)
        self.page.locator("input[placeholder*='密码']").fill(password)
        self.page.locator("input[placeholder*='验证码']").fill(verify_code)
        
        logger.info("表单已填写，点击登录...")
        self.click(self.LOGIN_BUTTON, "登录按钮")
        
        # 等待登录响应（关键：需要等待页面跳转或弹窗）
        import time
        for i in range(10):
            time.sleep(0.5)
            current_url = self.page.url
            logger.info(f"等待登录... ({i+1}/10) URL: {current_url}")
            
            # 如果检测到身份选择对话框
            if "您有多身份" in self.page.content():
                logger.info("检测到身份选择对话框")
                break
            
            # 如果 URL 变化了
            if "login" not in current_url:
                logger.info(f"URL 已变化：{current_url}")
                break
        
        # 处理身份选择
        if self.is_identity_select_visible():
            logger.info("处理身份选择...")
            if identity:
                self.select_identity_if_needed(identity)
            else:
                # 获取可用身份列表，选择第一个
                identities = self.get_available_identities()
                if identities:
                    self.select_identity_if_needed(identities[0])
                else:
                    self.select_identity_if_needed()
        
        return self
    
    def is_logged_in(self) -> bool:
        """检查是否登录成功"""
        try:
            # 等待页面跳转（新环境 URL 可能不同）
            self.page.wait_for_url("**/dataapp/**", timeout=5000)
            
            # 确认不在登录页
            current_url = self.page.url
            if "login" in current_url:
                logger.error(f"仍在登录页：{current_url}")
                return False
            
            logger.info(f"登录成功，页面已跳转到：{current_url}")
            return True
        except Exception as e:
            logger.error(f"登录可能失败：{e}")
            logger.debug(f"当前 URL: {self.page.url}")
            return False
    
    def get_error_message(self) -> str:
        """获取错误消息"""
        try:
            return self.get_text(self.ERROR_MESSAGE, "错误消息")
        except:
            return ""
    
    def is_verify_code_visible(self) -> bool:
        """检查验证码是否可见"""
        return self.is_visible(self.VERIFY_CODE_IMAGE, "验证码图片")
    
    # ===== 身份选择功能（登录的后续动作）=====
    
    def is_identity_select_visible(self) -> bool:
        """检查身份选择对话框是否显示"""
        try:
            return self.page.locator("text=您有多身份，请选择").is_visible(timeout=2000)
        except:
            return False
    
    def is_identity_select_page(self) -> bool:
        """检查是否需要选择身份（兼容旧方法）"""
        return self.is_identity_select_visible()
    
    def get_available_identities(self) -> List[str]:
        """获取所有可用身份列表"""
        try:
            buttons = self.page.locator("button, div[role='button']").all()
            identities = []
            
            for btn in buttons:
                text = btn.inner_text().strip()
                if text and len(text) > 2 and ("管理员" in text or "教师" in text or "学生" in text):
                    identities.append(text)
            
            logger.info(f"可用身份：{identities}")
            return identities
        except Exception as e:
            logger.error(f"获取身份列表失败：{e}")
            return []
    
    def select_identity_if_needed(self, identity: Optional[str] = None) -> bool:
        """
        如果需要选择身份，则选择
        
        Args:
            identity: 身份名称（可选，不传则选择第一个）
        
        Returns:
            bool: 是否成功选择
        """
        # 检查是否显示身份选择
        if not self.is_identity_select_visible():
            logger.debug("不需要选择身份")
            return True
        
        # 选择身份
        try:
            if identity:
                logger.info(f"选择身份：{identity}")
                self.page.locator(f"text={identity}").click()
            else:
                logger.info("选择第一个身份")
                self.page.locator("button, div[role='button']").first.click()
            
            # 等待页面跳转
            self.page.wait_for_url("**/dataapp/**", timeout=5000)
            logger.info("身份选择完成")
            return True
        except Exception as e:
            logger.error(f"选择身份失败：{e}")
            return False
    
    def select_identity(self, identity: str) -> bool:
        """
        选择指定身份（兼容旧方法）
        
        Args:
            identity: 身份名称
        
        Returns:
            bool: 是否成功选择
        """
        return self.select_identity_if_needed(identity)
