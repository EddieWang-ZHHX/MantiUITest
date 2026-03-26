"""示例页面对象 - 可根据实际项目修改"""
from .base_page import BasePage
from playwright.sync_api import Page


class ExamplePage(BasePage):
    """示例页面 - 登录页"""
    
    # 元素定位器
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login-btn"
    ERROR_MESSAGE = ".error-message"
    SUCCESS_MESSAGE = ".success-message"
    
    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url)
    
    def open_login_page(self) -> "ExamplePage":
        """打开登录页面"""
        return self.open("/login")
    
    def login(self, username: str, password: str) -> "ExamplePage":
        """执行登录"""
        (self
         .fill(self.USERNAME_INPUT, username, "用户名")
         .fill(self.PASSWORD_INPUT, password, "密码")
         .click(self.LOGIN_BUTTON, "登录按钮"))
        return self
    
    def get_error_message(self) -> str:
        """获取错误消息"""
        return self.get_text(self.ERROR_MESSAGE, "错误消息")
    
    def get_success_message(self) -> str:
        """获取成功消息"""
        return self.get_text(self.SUCCESS_MESSAGE, "成功消息")
    
    def is_login_button_visible(self) -> bool:
        """检查登录按钮是否可见"""
        return self.is_visible(self.LOGIN_BUTTON, "登录按钮")
