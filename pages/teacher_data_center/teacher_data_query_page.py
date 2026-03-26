"""教师数据查询页面对象"""
from pages.base_page import BasePage
from playwright.sync_api import Page
from utils.logger import logger


class TeacherDataQueryPage(BasePage):
    """教师数据查询页面"""
    
    # 搜索表单
    SEARCH_KEYWORD = 'input[placeholder="请输入姓名/工号"]'  # 关键字搜索
    SEARCH_BUTTON = 'button:has-text("查询")'  # 查询按钮
    RESET_BUTTON = 'button:has-text("重置")'  # 重置按钮
    MORE_CONDITIONS = 'button:has-text("更多条件")'  # 更多条件
    
    # 下拉选择器
    DEPARTMENT_SELECT = 'text=所属机构 >> xpath=ancestor::*[contains(@class,"select")]//input'
    EMPLOYMENT_TYPE_SELECT = 'text=用人方式'
    STATUS_SELECT = 'text=当前状态'
    
    # 表格
    DATA_TABLE = '[role="table"], table, .data-table'
    TABLE_ROW = '[role="row"], tr'
    ROW_COUNT_TEXT = 'text=共'
    
    # 角色列
    ROLE_COLUMN = '[role="cell"]:has-text("T-")'
    
    # 分页
    PAGINATION = '[role="navigation"]'
    PAGE_INPUT = 'input[type="number"]'
    PAGE_SIZE_SELECT = 'text=条/页'
    
    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url)
    
    def navigate_to(self) -> "TeacherDataQueryPage":
        """导航到教师数据查询页面"""
        return self.open("/index#/jssjzx/grsjzx/jssjcx")
    
    def search_by_keyword(self, keyword: str) -> "TeacherDataQueryPage":
        """按关键字搜索"""
        self.fill(self.SEARCH_KEYWORD, keyword, "关键字输入框")
        self.click(self.SEARCH_BUTTON, "查询按钮")
        self.page.wait_for_load_state("networkidle", timeout=10000)
        return self
    
    def reset(self) -> "TeacherDataQueryPage":
        """重置搜索条件"""
        self.click(self.RESET_BUTTON, "重置按钮")
        self.wait_for_timeout(500)
        return self
    
    def get_table_row_count(self) -> int:
        """获取表格行数"""
        try:
            text = self.page.locator('body').text_content()
            # 匹配 "共 X 条"
            import re
            match = re.search(r'共\s*(\d+)\s*条', text)
            if match:
                count = int(match.group(1))
                logger.info(f"表格共有 {count} 条数据")
                return count
            return 0
        except Exception as e:
            logger.error(f"获取行数失败：{e}")
            return 0
    
    def is_page_loaded(self) -> bool:
        """检查页面是否加载"""
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
            # 检查是否有查询按钮
            return self.is_visible('button:has-text("查询")', "查询按钮")
        except:
            return False
