"""登录测试"""
import pytest
from utils.logger import logger
from config.settings import Settings


class TestLogin:
    """登录测试类"""
    
    @pytest.mark.p1
    def test_login_success(self, login_page):
        """
        TC-LOGIN-001: 验证登录功能正常（默认身份：信息中心管理员）
        
        优先级: P1
        
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
    
    @pytest.mark.p2
    def test_login_with_wrong_password(self, login_page):
        """
        TC-LOGIN-002: 验证错误密码登录失败
        
        优先级: P2
        
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
        
        # 直接用 Playwright 点击（不走 login() 的等待循环，toast 会出现）
        login_page.page.locator('input[placeholder*="用户名"]').fill('T100002')
        login_page.page.locator('input[placeholder*="密码"]').fill('wrong_password')
        login_page.page.locator('input[placeholder*="验证码"]').fill('2222')
        login_page.page.locator('button:has-text("登录")').click()
        
        # 等待 toast 出现（很短时间）
        login_page.page.wait_for_timeout(500)
        
        # 检查 toast
        page_content = login_page.page.evaluate('document.body.innerText')
        assert "用户名或密码错误" in page_content, \
            f"未检测到登录失败提示，实际页面内容：{page_content[:200]}"
        
        logger.info("登录失败提示：用户名或密码错误，请重试！")
        logger.info("========== 测试通过：错误密码登录 ==========")
