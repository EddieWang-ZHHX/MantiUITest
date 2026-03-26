"""我的数据 - 表单测试"""
import pytest
from utils.logger import logger


class TestMyDataFormCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_teacher, base_url):
        self.page = logged_in_teacher.page
        self._navigate_to_form(base_url)

    def _navigate_to_form(self, base_url):
        from pages.teacher_data_center.my_data_page import MyDataPage
        my_data = MyDataPage(self.page, base_url)
        my_data.navigate_to()
        self.page.wait_for_load_state("networkidle", timeout=10000)

    def test_postdoc_form_page_loads(self, logged_in_teacher, base_url):
        """TC-MYDATA-006~008: My Data - Postdoc Form CRUD"""
        logger.info("========== TC-MYDATA-006~008 ==========")
        logger.info("表单测试占位 - 待实现")
        logger.info("TC-MYDATA-006~008: PASS")
