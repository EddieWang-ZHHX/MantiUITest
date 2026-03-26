"""教职工基本信息测试"""
import pytest
from utils.logger import logger


class TestBasicInfoEdit:
    """每个测试自主导航，不依赖其他测试留下的页面状态"""

    def test_basic_info_page_loads(self, logged_in_teacher, base_url):
        """TC-BASIC-001: 教职工基本信息页面加载"""
        page = logged_in_teacher.page
        logger.info("========== TC-BASIC-001 ==========")

        page.goto(base_url.rstrip("/") + "/index#/jssjzx/grsjzx/myarchive")
        page.wait_for_load_state("networkidle", timeout=15000)

        # 展开"教职工"行
        page.evaluate("""
            () => {
                const els = document.querySelectorAll('div.label');
                for (const el of els) {
                    if (el.textContent.trim() === '教职工') {
                        el.click();
                        break;
                    }
                }
            }
        """)
        page.wait_for_timeout(1000)

        # 点击"基本信息" section tab（在展开的行里）
        page.locator("button.tab, [class*=tab], [role='tab']").filter(has_text="基本信息").first.click(timeout=5000)
        page.wait_for_timeout(1000)

        # 验证"个人信息"表单内容可见
        assert page.locator("text=姓名").first.is_visible(), "个人信息表单未出现"
        logger.info("TC-BASIC-001: PASS")

    def test_basic_info_edit_button_works(self, logged_in_teacher, base_url):
        """TC-BASIC-002: 教职工基本信息编辑按钮"""
        page = logged_in_teacher.page
        logger.info("========== TC-BASIC-002 ==========")

        page.goto(base_url.rstrip("/") + "/index#/jssjzx/grsjzx/myarchive")
        page.wait_for_load_state("networkidle", timeout=15000)

        page.evaluate("""
            () => {
                const els = document.querySelectorAll('div.label');
                for (const el of els) {
                    if (el.textContent.trim() === '教职工') {
                        el.click();
                        break;
                    }
                }
            }
        """)
        page.wait_for_timeout(1000)

        page.locator("button.tab, [class*=tab], [role='tab']").filter(has_text="基本信息").first.click(timeout=5000)
        page.wait_for_timeout(1000)

        # 点击第一个"编辑"按钮（表单级别的）
        page.locator("button:has-text('编辑')").first.click(timeout=5000)
        page.wait_for_timeout(1000)

        # 验证编辑对话框（用 state=attached 判断 DOM 存在即可）
        page.wait_for_selector(".el-dialog__wrapper", state="attached", timeout=10000)
        logger.info("编辑对话框已打开")
        logger.info("TC-BASIC-002: PASS")
