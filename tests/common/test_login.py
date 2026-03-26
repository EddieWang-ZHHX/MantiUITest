"""登录测试"""
import pytest
from utils.logger import logger
from utils.debugger import StructuredDebugger
from config.settings import Settings


class TestLogin:
    """登录测试类"""
    
    def test_login_success(self, login_page):
        """
        TC-LOGIN-001: 验证登录功能正常（默认身份：信息中心管理员）

        【验证方式】（如何判断登录"工作正常"）
        验证点 1: URL 从 /login 跳转到 /dataapp/ 且不含 "login" 字符串
        验证点 2: 页面包含"退出"按钮（表示登录态）
        验证点 3: 无错误提示弹窗或红字提示
        验证点 4: 身份选择后跳转到正确的首页

        前置条件:
        - 测试账号 T100002 存在且密码为 wisedu@1
        - 测试环境验证码固定为 2222
        - 账号有多身份，默认识别为"信息中心管理员"

        测试步骤:
        1. 打开登录页面
        2. 输入用户名 T100002
        3. 输入密码 wisedu@1
        4. 输入验证码 2222
        5. 点击登录按钮
        6. 选择身份"信息中心管理员"（如果弹窗出现）

        预期结果:
        1. URL 跳转到 /dataapp/ 相关路径，不含 "login"
        2. 页面包含"退出"按钮或用户信息
        3. 无错误提示
        4. 页面正常渲染，无白屏或 loading 一直转

        失败自检清单:
        Critical:
          - [ ] 定位器是否在页面分析文档里验证过？
          - [ ] 预期结果是否符合实际页面能力（URL 格式、按钮文字）？
        Warning:
          - [ ] 测试是否独立（不依赖其他用例的状态）？
          - [ ] 测试数据是否稳定（T100002 是否被占用）？
        Note:
          - [ ] 证据收集配置是否正确？（trace: always）
          - [ ] 是否有对应的页面分析文档？
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
        
        # 等待页面真正跳转完成（避免在身份选择弹窗阶段就开始验证）
        login_page.page.wait_for_url("**/dataapp/**", timeout=10000)
        
        # ===== 验证方式 =====
        # 验证点 1: URL 跳转正确
        current_url = login_page.page.url
        assert "/login" not in current_url, \
            f"验证失败：URL 仍在登录页 {current_url}"
        
        # 验证点 2: 页面包含退出按钮（登录态标志）
        # 注意：先尝试多种可能的选择器
        has_exit_button = (
            login_page.is_visible("text=退出", "退出按钮") or
            login_page.is_visible("button:has-text('退出')", "退出按钮") or
            login_page.is_visible("text=信息中心管理员", "身份标识")
        )
        assert has_exit_button, \
            f"验证失败：页面未包含退出按钮或身份标识，当前 URL: {current_url}"
        
        # 验证点 3: 无错误提示
        error_visible = login_page.is_visible(".error-message, .msg-error, .tips-error", "错误提示")
        assert not error_visible, \
            f"验证失败：页面显示了错误提示"
        
        logger.info("========== 测试通过：登录成功 ==========")
    
    def test_login_fail(self, login_page):
        """
        TC-LOGIN-002: 验证错误密码登录失败

        【验证方式】（如何判断"登录失败"）
        验证点 1: 页面不跳转到 /dataapp/，URL 仍包含 "login"
        验证点 2: 页面显示错误提示（"密码错误"或类似）
        验证点 3: 页面不包含"退出"按钮

        前置条件:
        - 测试账号 T100002 存在

        测试步骤:
        1. 打开登录页面
        2. 输入用户名 T100002
        3. 输入错误密码 wrong_password
        4. 输入验证码 2222
        5. 点击登录按钮

        预期结果:
        1. URL 仍为登录页（包含 "login"）
        2. 显示错误提示信息
        3. 不出现身份选择弹窗
        4. 不出现"退出"按钮

        失败自检清单:
        Critical:
          - [ ] 定位器是否正确？（错误提示元素的 class/name 是否匹配）
        Warning:
          - [ ] 测试环境验证码是否固定为 2222？
        Note:
          - [ ] 错误提示文字是否和页面实际显示一致？
        """
        logger.info("========== 开始测试：错误密码登录 ==========")
        
        # 打开登录页面
        login_page.open_login()
        
        # 执行登录（错误密码）
        # login() 方法内部会检测 Toast 并设置 _login_failed 标志
        login_page.login(
            username="T100002",
            password="wrong_password",
            verify_code="2222"
        )
        
        # ===== 验证方式 =====
        # 验证点 1: URL 不跳转（仍在登录页）
        current_url = login_page.page.url
        assert "login" in current_url, \
            f"验证失败：登录失败但页面跳转了，当前 URL: {current_url}"
        
        # 验证点 2: login() 方法检测到错误提示 Toast
        assert login_page._login_failed, \
            f"验证失败：未检测到错误提示Toast（用户名或密码错误），当前 URL: {current_url}"
        
        # 验证点 3: 不出现退出按钮（登录失败不会有登录态）
        has_exit = (
            login_page.is_visible("text=退出", "退出按钮") or
            login_page.is_visible("button:has-text('退出')", "退出按钮")
        )
        assert not has_exit, \
            f"验证失败：登录失败但出现了退出按钮"
        
        logger.info(f"登录失败，页面仍在：{current_url}")
        logger.info("========== 测试通过：错误密码登录 ==========")
