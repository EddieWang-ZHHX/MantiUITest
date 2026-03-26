"""报告展示演示测试 - 故意制造失败场景验证报告"""

import pytest
from utils.logger import logger


def test_demo_pass(logged_in_admin, base_url):
    """TC-DEMO-001: 演示通过用例"""
    page = logged_in_admin.page
    page.goto(base_url.rstrip("/") + "/index#/jssjzx/grsjzx/myarchive")
    page.wait_for_load_state("networkidle", timeout=15000)
    assert page.locator("body").first.is_visible(), "PASS：演示通过用例"
    logger.info("TC-DEMO-001: PASS")


def test_demo_fail(logged_in_admin, base_url):
    """TC-DEMO-002: 演示失败用例（故意失败）"""
    page = logged_in_admin.page
    page.goto(base_url.rstrip("/") + "/index#/jssjzx/grsjzx/myarchive")
    page.wait_for_load_state("networkidle", timeout=15000)
    # 故意断言失败：找一个不存在的元素
    assert page.locator("div.this_element_does_not_exist_12345").is_visible(), "故意失败：TC-DEMO-002"
    logger.info("TC-DEMO-002: 这行不会打印")
