"""教师数据查询测试"""
import pytest
from utils.logger import logger


def test_teacher_query_page_visible(logged_in_admin, base_url):
    """TC-100260: 教师数据查询页面可见"""
    page = logged_in_admin.page
    from pages.teacher_data_center.teacher_data_query_page import TeacherDataQueryPage

    logger.info("========== TC-100260 ==========")
    query = TeacherDataQueryPage(page, base_url)
    query.navigate_to()

    # 验证页面 URL
    assert "jssjcx" in page.url or "dataapp" in page.url, f"URL: {page.url}"
    logger.info(f"页面 URL: {page.url}")
    logger.info("TC-100260: PASS")
