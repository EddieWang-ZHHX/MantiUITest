"""登录测试 - 带身份选择"""
import pytest
from utils.logger import logger


class TestLoginWithIdentity:
    """带身份选择的登录测试"""
    
    @pytest.mark.parametrize("identity", [
        "信息中心管理员",
        # "教师",  # 如果有教师账号可以添加
        # "人事处管理员",
    ])
    @pytest.mark.p1
    def test_login_with_identity(self, login_page, identity):
        """
        TC-LOGIN-003: 验证不同身份登录
        
        优先级: P1
        
        测试步骤:
        1. 打开登录页面
        2. 输入用户名、密码、验证码
        3. 点击登录
        4. 选择指定身份
        
        预期结果:
        1. 登录成功，页面跳转到对应身份的主页
        
        参数:
            identity: 要选择的身份
        """
        logger.info(f"========== 开始测试：登录并选择身份 [{identity}] ==========")
        
        # 打开登录页面
        login_page.open_login()
        
        # 执行登录（不传 identity，让 login 自己处理）
        login_page.login(
            username="T100002",
            password="wisedu@1",
            verify_code="2222",
            identity=identity  # 传递 identity 参数
        )
        
        # 验证登录成功
        assert login_page.is_logged_in(), f"登录失败，页面未跳转（身份：{identity}）"
        
        logger.info(f"========== 测试通过：登录并选择身份 [{identity}] ==========")
    
    @pytest.mark.p3
    def test_login_select_first_identity(self, login_page):
        """
        TC-LOGIN-004: 验证登录并选择第一个可用身份
        
        优先级: P3
        
        测试步骤:
        1. 打开登录页面
        2. 输入用户名、密码、验证码
        3. 点击登录
        4. 选择第一个可用身份
        
        预期结果:
        1. 登录成功
        """
        logger.info("========== 开始测试：登录并选择第一个身份 ==========")
        
        # 打开登录页面
        login_page.open_login()
        
        # 执行登录
        login_page.login(
            username="T100002",
            password="wisedu@1",
            verify_code="2222"
        )
        
        # 如果需要选择身份，选择第一个
        if login_page.is_identity_select_page():
            logger.info("选择第一个可用身份")
            # 获取所有可用身份
            # 点击第一个身份按钮
            login_page.page.locator("button, div[role='button']").first.click()
        
        # 验证登录成功
        assert login_page.is_logged_in(), "登录失败，页面未跳转"
        
        logger.info("========== 测试通过：登录并选择第一个身份 ==========")
