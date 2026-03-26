"""页面对象基类"""
from playwright.sync_api import Page, Locator, expect
from typing import Optional, List
from utils.logger import logger


class BasePage:
    """所有页面对象的基类"""
    
    def __init__(self, page: Page, base_url: str = ""):
        self.page = page
        self.base_url = base_url
    
    def open(self, url: str = "") -> "BasePage":
        """打开页面"""
        full_url = self.base_url + url if url.startswith("/") else url
        logger.info(f"打开页面：{full_url}")
        self.page.goto(full_url)
        return self
    
    def click(self, selector: str, description: str = "元素") -> "BasePage":
        """点击元素"""
        logger.debug(f"点击 {description}: {selector}")
        locator = self.page.locator(selector)
        locator.click()
        return self
    
    def fill(self, selector: str, value: str, description: str = "输入框") -> "BasePage":
        """填充输入框"""
        logger.debug(f"填充 {description}: {selector} = {value}")
        locator = self.page.locator(selector)
        locator.fill(value)
        return self
    
    def get_text(self, selector: str, description: str = "元素") -> str:
        """获取元素文本"""
        locator = self.page.locator(selector)
        text = locator.text_content()
        logger.debug(f"{description} 文本：{text}")
        return text
    
    def is_visible(self, selector: str, description: str = "元素") -> bool:
        """检查元素是否可见"""
        locator = self.page.locator(selector)
        return locator.is_visible()
    
    def is_enabled(self, selector: str, description: str = "元素") -> bool:
        """检查元素是否可用"""
        locator = self.page.locator(selector)
        return locator.is_enabled()
    
    def wait_for_element(self, selector: str, state: str = "visible", timeout: int = None) -> Locator:
        """等待元素状态"""
        locator = self.page.locator(selector)
        locator.wait_for(state=state, timeout=timeout)
        return locator
    
    def expect_text(self, selector: str, expected_text: str, description: str = "元素"):
        """断言元素文本"""
        locator = self.page.locator(selector)
        expect(locator).to_have_text(expected_text)
        logger.info(f"✓ 断言 {description} 文本正确：{expected_text}")
    
    def expect_visible(self, selector: str, description: str = "元素"):
        """断言元素可见"""
        locator = self.page.locator(selector)
        expect(locator).to_be_visible()
        logger.info(f"✓ 断言 {description} 可见")
    
    def expect_url(self, expected_url: str):
        """断言 URL"""
        expect(self.page).to_have_url(expected_url)
        logger.info(f"✓ 断言 URL 正确：{expected_url}")
    
    def screenshot(self, path: str, full_page: bool = False):
        """截图"""
        self.page.screenshot(path=path, full_page=full_page)
        logger.debug(f"截图保存：{path}")
    
    def hover(self, selector: str, description: str = "元素") -> "BasePage":
        """悬停元素"""
        locator = self.page.locator(selector)
        locator.hover()
        logger.debug(f"悬停 {description}: {selector}")
        return self
    
    def select_option(self, selector: str, value: str, description: str = "下拉框") -> "BasePage":
        """选择下拉选项"""
        locator = self.page.locator(selector)
        locator.select_option(value)
        logger.debug(f"选择 {description} 选项：{value}")
        return self
    
    def check(self, selector: str, description: str = "复选框") -> "BasePage":
        """勾选复选框"""
        locator = self.page.locator(selector)
        locator.check()
        logger.debug(f"勾选 {description}: {selector}")
        return self
    
    def uncheck(self, selector: str, description: str = "复选框") -> "BasePage":
        """取消勾选复选框"""
        locator = self.page.locator(selector)
        locator.uncheck()
        logger.debug(f"取消勾选 {description}: {selector}")
        return self
