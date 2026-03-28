from playwright.sync_api import sync_playwright, Page, Browser
from datetime import datetime
from typing import Optional, List
import time

from utils.parsers.base_parser import BaseParser, PageSnapshot, ElementInfo


class PlaywrightParser(BaseParser):
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._playwright = None

    def parse(self, source: str, **kwargs) -> PageSnapshot:
        url = source
        login_info = kwargs.get("login_info")
        existing_context = kwargs.get("context")

        if existing_context:
            page = existing_context.new_page()
            page.goto(url, timeout=self.timeout)
            page.wait_for_load_state("networkidle", timeout=self.timeout)
            # SPA 页面需要额外等待内容加载
            self._wait_for_content(page)
        else:
            self._start_browser()
            self._page.goto(url, timeout=self.timeout)
            self._page.wait_for_load_state("networkidle", timeout=self.timeout)
            # SPA 页面需要额外等待内容加载
            self._wait_for_content(self._page)
            page = self._page

        title = self._get_title(page)
        elements = self._extract_elements(page)
        inputs, buttons, links, forms = self._group_elements(elements)

        snapshot = PageSnapshot(
            url=url,
            title=title,
            explored_at=datetime.now().isoformat(),
            parser="playwright",
            elements=elements,
            forms=forms,
            buttons=buttons,
            links=links,
            inputs=inputs,
        )

        if not existing_context:
            self._close_browser()

        return snapshot

    def _wait_for_content(self, page, max_wait: int = 10):
        """
        智能等待页面内容加载
        对于 SPA 页面，需要等待内容动态渲染
        """
        import time
        
        # 等待策略：
        # 1. 等待常见的加载指示器消失
        # 2. 等待页面内容区域出现
        # 3. 轮询检查元素数量是否稳定
        
        start_time = time.time()
        last_count = 0
        stable_count = 0
        
        while time.time() - start_time < max_wait:
            try:
                # 尝试等待常见的内容容器
                content_selectors = [
                    ".el-main",  # Element UI 主内容区
                    ".main-content",
                    ".content-wrapper",
                    "[role='main']",
                    ".app-main",
                ]
                
                for selector in content_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            # 找到内容容器，等待其内部元素加载
                            time.sleep(0.5)
                            break
                    except:
                        continue
                
                # 检查元素数量是否稳定
                current_count = page.locator("input, button, a, select, textarea").count()
                
                if current_count > 0 and current_count == last_count:
                    stable_count += 1
                    if stable_count >= 2:  # 连续 2 次数量相同，认为加载完成
                        break
                else:
                    stable_count = 0
                
                last_count = current_count
                time.sleep(0.5)
                
            except Exception as e:
                time.sleep(0.5)
                continue

    def _start_browser(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=["--start-maximized", "--disable-notifications"],
        )
        context = self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        self._page = context.new_page()
        self._page.set_default_timeout(self.timeout)

    def _close_browser(self):
        if self._page:
            self._page.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _get_title(self, page: Page) -> str:
        try:
            return page.title()
        except:
            return ""

    def _extract_elements(self, page: Page) -> List[ElementInfo]:
        elements = []
        tags = ["input", "button", "a", "select", "textarea"]

        for tag in tags:
            try:
                locators = page.locator(tag).all()
                for idx, locator in enumerate(locators):
                    try:
                        if not locator.is_visible():
                            continue
                    except:
                        continue

                    attrs = self._get_attributes(locator, tag)
                    text = self._get_text(locator, tag)
                    selectors = self._generate_selectors(tag, attrs, text)
                    stability = self._assess_stability(
                        selectors[0] if selectors else ""
                    )
                    group = self._get_group(tag)

                    element = ElementInfo(
                        tag=tag,
                        attrs=attrs,
                        selector=selectors[0]
                        if selectors
                        else f"{tag}:nth-of-type({idx})",
                        selector_candidates=selectors,
                        stability=stability,
                        group=group,
                        text=text,
                    )
                    elements.append(element)
            except Exception as e:
                continue

        return elements

    def _get_attributes(self, locator, tag: str) -> dict:
        attrs = {}
        attr_names = [
            "placeholder",
            "name",
            "id",
            "type",
            "aria-label",
            "class",
            "role",
            "data-id",
            "title",
        ]

        for attr in attr_names:
            try:
                val = locator.get_attribute(attr)
                if val is not None:
                    attrs[attr] = val
            except:
                pass

        try:
            input_type = locator.get_attribute("type")
            if input_type:
                attrs["type"] = input_type
        except:
            pass

        return attrs

    def _get_text(self, locator, tag: str) -> str:
        try:
            if tag in ["button", "a", "span", "div"]:
                return locator.inner_text().strip()
            elif tag == "input":
                return ""
            else:
                return locator.inner_text().strip()
        except:
            return ""

    def close(self):
        self._close_browser()
