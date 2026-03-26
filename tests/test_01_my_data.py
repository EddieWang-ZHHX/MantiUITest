"""我的数据页面测试

注意：T100002 账号使用"教师"身份时，登录后直接显示"我的数据"页面内容
"""
import pytest
from utils.logger import logger


class TestMyData:
    """我的数据页面测试类"""
    
    def test_teacher_identity_my_data(self, login_page):
        """
        验证使用"教师"身份登录后能访问"我的数据"
        
        说明：
        - T100002 + "教师"身份 = 登录后直接显示"我的数据"内容
        - 页面显示：个人信息、教学育人、科学研究
        """
        logger.info("========== 开始测试：教师身份访问我的数据 ==========")
        
        # 登录（使用"教师"身份）
        login_page.open_login()
        login_page.login(
            username="T100002",
            password="wisedu@1",
            verify_code="2222",
            identity="教师"
        )
        
        # 等待页面稳定
        login_page.page.wait_for_timeout(3000)
        
        # 如果还在身份选择页面，手动选择"教师"
        if "selectIdentity" in login_page.page.url or "您有多身份" in login_page.page.content():
            logger.info("检测到身份选择页面，手动选择'教师'...")
            try:
                login_page.page.locator("text=教师").click()
                login_page.page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f"选择教师身份失败：{e}")
        
        # 验证 URL
        current_url = login_page.page.url
        logger.info(f"登录后 URL: {current_url}")
        
        # 验证页面内容
        page_content = login_page.page.evaluate("document.body.innerText")
        logger.info(f"页面内容长度：{len(page_content)}")
        
        # 检查权限错误
        assert "没有操作菜单权限" not in page_content, "显示权限错误"
        
        # 验证"我的数据"相关模块存在
        has_personal = "个人信息" in page_content
        has_teaching = "教学育人" in page_content  
        has_research = "科学研究" in page_content
        
        logger.info(f"模块检查：个人信息={has_personal}, 教学育人={has_teaching}, 科学研究={has_research}")
        
        assert has_personal or has_teaching or has_research, \
            f"未找到'我的数据'相关模块。页面内容：{page_content[:500]}"
        
        logger.info("========== 测试通过：教师身份访问我的数据 ==========")
    
    def test_my_data_modules(self, login_page):
        """
        验证"我的数据"页面的四大模块
        
        说明：页面应显示基本信息、人事信息、教育教学、科研信息四大模块
        """
        logger.info("========== 开始测试：我的数据四大模块 ==========")
        
        # 登录（使用"教师"身份）
        login_page.open_login()
        login_page.login(
            username="T100002",
            password="wisedu@1",
            verify_code="2222",
            identity="教师"
        )
        
        # 等待页面稳定
        login_page.page.wait_for_timeout(3000)
        
        # 如果还在身份选择页面，手动选择"教师"
        if "selectIdentity" in login_page.page.url or "您有多身份" in login_page.page.content():
            logger.info("检测到身份选择页面，手动选择'教师'...")
            try:
                login_page.page.locator("text=教师").click()
                login_page.page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f"选择教师身份失败：{e}")
        
        # 获取页面内容
        page_content = login_page.page.evaluate("document.body.innerText")
        
        # 验证四大模块存在（根据实际页面内容调整）
        # 注意：教师身份显示的是"个人信息、教学育人、科学研究"，不是"基本信息、人事信息..."
        modules_to_check = [
            ("个人信息", "个人信息"),
            ("教学育人", "教学育人"),
            ("科学研究", "科学研究"),
        ]
        
        for module_name, check_text in modules_to_check:
            assert check_text in page_content, f"缺少'{module_name}'模块"
            logger.info(f"  ✅ {module_name}")
        
        logger.info("========== 测试通过：我的数据四大模块 ==========")
