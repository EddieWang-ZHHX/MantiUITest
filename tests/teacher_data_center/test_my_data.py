"""我的数据页面测试"""
import pytest
from utils.logger import logger


def test_my_data_page_visible(logged_in_teacher, base_url):
    """TC-100269: 我的数据页面可见"""
    page = logged_in_teacher.page
    from pages.teacher_data_center.my_data_page import MyDataPage

    logger.info("========== TC-100269 ==========")
    my_data = MyDataPage(page, base_url)
    my_data.navigate_to()

    # 验证页面 URL
    assert "myarchive" in page.url or "jssjzx" in page.url, f"URL: {page.url}"
    logger.info(f"页面 URL: {page.url}")
    logger.info("TC-100269: PASS")


def test_demo_fail_added(logged_in_teacher, base_url):
    """TC-DEMO-003: 演示失败用例（故意失败）"""
    page = logged_in_teacher.page
    page.goto(base_url.rstrip("/") + "/index#/jssjzx/grsjzx/myarchive")
    page.wait_for_load_state("networkidle", timeout=15000)
    assert page.locator("div.this_element_does_not_exist_999").is_visible(), "故意失败：TC-DEMO-003"


def test_demo_fail_added(logged_in_teacher, base_url):
    """TC-DEMO-003: 演示失败用例（故意失败）"""
    page = logged_in_teacher.page
    page.goto(base_url.rstrip("/") + "/index#/jssjzx/grsjzx/myarchive")
    page.wait_for_load_state("networkidle", timeout=15000)
    assert page.locator("div.this_element_does_not_exist_999").is_visible(), "故意失败"
