"""我的数据页面对象"""
from pages.base_page import BasePage
from playwright.sync_api import Page
from utils.logger import logger


class MyDataPage(BasePage):
    """我的数据页面"""
    
    # 元素定位器 - 需要根据实际页面调整
    # 四大模块
    BASIC_INFO_MODULE = ".basic-info-module"      # 基本信息
    HR_INFO_MODULE = ".hr-info-module"           # 人事信息
    EDUCATION_INFO_MODULE = ".education-info-module"  # 教育教学
    RESEARCH_INFO_MODULE = ".research-info-module"    # 科研信息
    
    # 数据卡片
    DATA_CARD = ".data-card"
    DATA_COUNT = ".data-count"
    
    # 菜单导航
    MENU_MY_DATA = ".menu-my-data"
    
    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url)
    
    def navigate_to(self) -> "MyDataPage":
        """导航到我的数据页面"""
        return self.open("/index#/jssjzx/grsjzx/myarchive/myarchive")
    
    def is_visible(self) -> bool:
        """检查页面是否可见"""
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
            return True
        except:
            return False
    
    def has_four_modules(self) -> bool:
        """检查是否有四大模块"""
        modules = [
            (self.BASIC_INFO_MODULE, "基本信息"),
            (self.HR_INFO_MODULE, "人事信息"),
            (self.EDUCATION_INFO_MODULE, "教育教学"),
            (self.RESEARCH_INFO_MODULE, "科研信息")
        ]
        
        for selector, name in modules:
            try:
                is_vis = self.page.locator(selector).is_visible(timeout=2000)
                if not is_vis:
                    logger.warning(f"模块 {name} 未找到 (selector: {selector})")
                    return False
            except Exception as e:
                logger.warning(f"检查模块 {name} 时出错：{e}")
                return False
        
        logger.info("四大模块都存在")
        return True
    
    def get_module_count(self, module_selector: str) -> int:
        """获取某个模块的数据数量"""
        try:
            locator = self.page.locator(module_selector)
            count = locator.count()
            logger.info(f"模块 {module_selector} 数据数量：{count}")
            return count
        except Exception as e:
            logger.error(f"获取数据数量失败：{e}")
            return 0
    
    def click_module(self, module_name: str) -> "MyDataPage":
        """点击某个模块查看详情"""
        module_map = {
            "basic": self.BASIC_INFO_MODULE,
            "hr": self.HR_INFO_MODULE,
            "education": self.EDUCATION_INFO_MODULE,
            "research": self.RESEARCH_INFO_MODULE
        }
        
        selector = module_map.get(module_name.lower())
        if selector:
            self.click(selector, f"{module_name}模块")
        
        return self
    
    def expand_all_modules(self) -> "MyDataPage":
        """展开所有模块"""
        # 假设有展开按钮
        expand_buttons = self.page.locator(".expand-btn")
        for i in range(expand_buttons.count()):
            expand_buttons.nth(i).click()
        
        logger.info("已展开所有模块")
        return self
    
    def collapse_all_modules(self) -> "MyDataPage":
        """收起所有模块"""
        # 假设有收起按钮
        collapse_buttons = self.page.locator(".collapse-btn")
        for i in range(collapse_buttons.count()):
            collapse_buttons.nth(i).click()
        
        logger.info("已收起所有模块")
        return self
