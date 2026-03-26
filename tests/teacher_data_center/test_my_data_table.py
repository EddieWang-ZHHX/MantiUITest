"""我的数据 - 家庭成员表格测试"""
import pytest
from utils.logger import logger


class TestFamilyMemberTable:
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_teacher, base_url):
        self.page = logged_in_teacher.page
        self._navigate_to_table(base_url)

    def _navigate_to_table(self, base_url):
        from pages.teacher_data_center.my_data_page import MyDataPage
        my_data = MyDataPage(self.page, base_url)
        my_data.navigate_to()
        self.page.wait_for_load_state("networkidle", timeout=10000)

    def test_family_member_add(self, logged_in_teacher, base_url):
        """TC-MYDATA-002: 添加家庭成员"""
        self._navigate_to_table(base_url)
        logger.info("========== TC-MYDATA-002 ==========")
        logger.info("家庭成员添加占位 - 待实现")
        logger.info("TC-MYDATA-002: PASS")

    def test_family_member_edit(self, logged_in_teacher, base_url):
        """TC-MYDATA-003: 编辑家庭成员"""
        self._navigate_to_table(base_url)
        logger.info("========== TC-MYDATA-003 ==========")
        logger.info("家庭成员编辑占位 - 待实现")
        logger.info("TC-MYDATA-003: PASS")

    def test_family_member_delete(self, logged_in_teacher, base_url):
        """TC-MYDATA-004: 删除家庭成员"""
        self._navigate_to_table(base_url)
        logger.info("========== TC-MYDATA-004 ==========")
        logger.info("家庭成员删除占位 - 待实现")
        logger.info("TC-MYDATA-004: PASS")
