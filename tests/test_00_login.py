"""登录测试"""
import pytest
from utils.logger import logger
from config.settings import Settings


class TestLogin:
    """登录测试类"""
    
    def test_login_success(self, login_page):
        """
        TC-LOGIN-001: 验证登录功能正常（默认身份：信息中心管理员）
        
        测试步骤:
        1. 打开登录页面
        2. 输入用户名、密码、验证码
        3. 点击登录
        4. 选择身份（如果需要）
        
        预期结果:
        1. 登录成功，页面跳转
        """
        logger.info("========== 开始测试：登录成功 ==========")
        
        # 打开登录页面
        login_page.open_login()
        
        # 执行登录
        login_page.login(
            username="T100002",
            password="wisedu@1",
            verify_code="2222"
        )
        
        # 如果需要选择身份，选择"信息中心管理员"
        login_page.select_identity_if_needed("信息中心管理员")
        
        # 验证登录成功
        assert login_page.is_logged_in(), "登录失败，页面未跳转"
        
        logger.info("========== 测试通过：登录成功 ==========")
    
    def test_login_with_wrong_password(self, login_page):
        """
        TC-LOGIN-002: 验证错误密码登录失败
        
        测试步骤:
        1. 打开登录页面
        2. 输入正确的用户名，错误的密码
        3. 点击登录
        
        预期结果:
        1. 登录失败，页面不跳转（仍在登录页）
        """
        logger.info("========== 开始测试：错误密码登录 ==========")
        
        # 打开登录页面
        login_page.open_login()
        
        # 执行登录（错误密码）
        login_page.login(
            username="T100002",
            password="wrong_password",
            verify_code="2222"
        )
        
        # 验证登录失败：页面应该还在登录页（URL 包含 login）
        current_url = login_page.page.url
        assert "login" in current_url, f"登录失败但页面跳转了：{current_url}"
        
        logger.info(f"登录失败，页面仍在：{current_url}")
        logger.info("========== 测试通过：错误密码登录 ==========")
