"""故意失败的测试 - 用于测试证据收集功能"""
import pytest
from utils.logger import logger


class TestFailDemo:
    """失败演示测试"""
    
    def test_always_fail(self, login_page):
        """
        这个测试必定失败，用于测试证据收集功能
        
        失败后可以：
        1. 点击控制台输出的 trace.zip 链接
        2. 查看截图、HTML 等证据
        """
        logger.info("========== 开始测试：这个测试会失败 ==========")
        
        # 故意让测试失败
        assert False, "这是一个故意失败的测试，用于验证证据收集功能"
    
    def test_navigation_fail(self, login_page):
        """
        导航到不存在的页面
        """
        logger.info("========== 开始测试：导航到不存在的页面 ==========")
        
        # 登录
        login_page.open_login()
        login_page.login(
            username="T100002",
            password="wisedu@1",
            verify_code="2222",
            identity="教师"
        )
        
        # 故意导航到错误的 URL
        login_page.page.goto("http://this-url-does-not-exist-12345.com")
        
        # 验证（会失败）
        assert "不存在" in login_page.page.title(), "页面应该显示 404"
