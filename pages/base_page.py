"""页面对象基类"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict

from playwright.sync_api import Page, Locator, expect
from utils.logger import logger


@dataclass
class SelectorRecord:
    """Selector 记录"""

    selector: str
    status: str = "untested"  # untested, verified, failed, quarantined
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    stability: str = "medium"  # high, medium, low
    candidates: List[str] = field(default_factory=list)  # 备选 selector 列表
    last_tested: Optional[str] = None

    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.successes / self.attempts

    def mark_success(self):
        self.attempts += 1
        self.successes += 1
        self.failures = 0
        self.status = "verified"
        self.last_tested = datetime.now().isoformat()

    def mark_failure(self):
        self.attempts += 1
        self.failures += 1
        self.last_tested = datetime.now().isoformat()

        if self.failures >= 3:
            self.status = "quarantined"


class BasePage:
    """
    所有页面对象的基类

    进化机制:
    1. 所有 Selector 存储在 SELECTORS_HISTORY 中
    2. 每次执行记录 success/failure
    3. 失败时自动回退到其他可用的候选 Selector
    4. 连续失败 3 次的 Selector 会被 quarantine
    """

    SELECTORS: Dict[str, str] = {}
    SELECTORS_HISTORY: Dict[str, SelectorRecord] = {}

    def __init__(self, page: Page, base_url: str = ""):
        self.page = page
        self.base_url = base_url

    @classmethod
    def get_selector(cls, name: str) -> str:
        """
        获取 selector，带进化回退机制

        优先级: verified -> untested -> failed (按成功率排序)
        """
        if name in cls.SELECTORS:
            return cls.SELECTORS[name]

        if name not in cls.SELECTORS_HISTORY:
            return name

        record = cls.SELECTORS_HISTORY[name]

        if record.status == "verified":
            return record.selector

        if record.status == "quarantined":
            return cls._fallback_to_candidates(name, record)

        if record.candidates:
            return cls._fallback_to_candidates(name, record)

        return record.selector

    @classmethod
    def _fallback_to_candidates(cls, name: str, record: SelectorRecord) -> str:
        """尝试候选 selectors"""
        for candidate in record.candidates:
            if candidate == record.selector:
                continue
            record.selector = candidate
            return candidate
        return record.selector

    @classmethod
    def record_success(cls, name: str):
        """记录成功"""
        if name not in cls.SELECTORS_HISTORY:
            return

        record = cls.SELECTORS_HISTORY[name]
        record.mark_success()
        logger.debug(
            f"Selector {name}: success ({record.success_rate():.1%}), status={record.status}"
        )

    @classmethod
    def record_failure(cls, name: str):
        """记录失败"""
        if name not in cls.SELECTORS_HISTORY:
            return

        record = cls.SELECTORS_HISTORY[name]
        record.mark_failure()
        logger.warning(
            f"Selector {name}: failed ({record.failures} consecutive), status={record.status}"
        )

    def _resolve_selector(self, name_or_selector: str) -> str:
        """解析 selector 名称或直接返回 selector"""
        if name_or_selector in self.SELECTORS_HISTORY:
            return self.get_selector(name_or_selector)
        return name_or_selector

    def open(self, url: str = "") -> "BasePage":
        """打开页面"""
        full_url = self.base_url + url if url.startswith("/") else url
        logger.info(f"打开页面：{full_url}")
        self.page.goto(full_url)
        return self

    def click(self, selector: str, description: str = "元素") -> "BasePage":
        """点击元素"""
        resolved = self._resolve_selector(selector)
        logger.debug(f"点击 {description}: {resolved}")
        try:
            self.page.locator(resolved).click()
            self._record_action(selector, success=True)
        except Exception as e:
            self._record_action(selector, success=False)
            raise
        return self

    def fill(
        self, selector: str, value: str, description: str = "输入框"
    ) -> "BasePage":
        """填充输入框"""
        resolved = self._resolve_selector(selector)
        logger.debug(f"填充 {description}: {resolved} = {value}")
        try:
            self.page.locator(resolved).fill(value)
            self._record_action(selector, success=True)
        except Exception as e:
            self._record_action(selector, success=False)
            raise
        return self

    def get_text(self, selector: str, description: str = "元素") -> str:
        """获取元素文本"""
        resolved = self._resolve_selector(selector)
        locator = self.page.locator(resolved)
        text = locator.text_content()
        logger.debug(f"{description} 文本：{text}")
        return text

    def is_visible(self, selector: str, description: str = "元素") -> bool:
        """检查元素是否可见"""
        resolved = self._resolve_selector(selector)
        return self.page.locator(resolved).is_visible()

    def is_enabled(self, selector: str, description: str = "元素") -> bool:
        """检查元素是否可用"""
        resolved = self._resolve_selector(selector)
        return self.page.locator(resolved).is_enabled()

    def wait_for_element(
        self, selector: str, state: str = "visible", timeout: int = None
    ) -> Locator:
        """等待元素状态"""
        resolved = self._resolve_selector(selector)
        locator = self.page.locator(resolved)
        locator.wait_for(state=state, timeout=timeout)
        return locator

    def expect_text(self, selector: str, expected_text: str, description: str = "元素"):
        """断言元素文本"""
        resolved = self._resolve_selector(selector)
        locator = self.page.locator(resolved)
        expect(locator).to_have_text(expected_text)
        logger.info(f"✓ 断言 {description} 文本正确：{expected_text}")

    def expect_visible(self, selector: str, description: str = "元素"):
        """断言元素可见"""
        resolved = self._resolve_selector(selector)
        locator = self.page.locator(resolved)
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
        resolved = self._resolve_selector(selector)
        locator = self.page.locator(resolved)
        locator.hover()
        logger.debug(f"悬停 {description}: {resolved}")
        return self

    def select_option(
        self, selector: str, value: str, description: str = "下拉框"
    ) -> "BasePage":
        """选择下拉选项"""
        resolved = self._resolve_selector(selector)
        locator = self.page.locator(resolved)
        locator.select_option(value)
        logger.debug(f"选择 {description} 选项：{value}")
        return self

    def check(self, selector: str, description: str = "复选框") -> "BasePage":
        """勾选复选框"""
        resolved = self._resolve_selector(selector)
        locator = self.page.locator(resolved)
        locator.check()
        logger.debug(f"勾选 {description}: {resolved}")
        return self

    def uncheck(self, selector: str, description: str = "复选框") -> "BasePage":
        """取消勾选"""
        resolved = self._resolve_selector(selector)
        locator = self.page.locator(resolved)
        locator.uncheck()
        logger.debug(f"取消勾选 {description}: {resolved}")
        return self

    def _record_action(self, name_or_selector: str, success: bool):
        """记录动作结果"""
        if name_or_selector in self.SELECTORS_HISTORY:
            if success:
                self.record_success(name_or_selector)
            else:
                self.record_failure(name_or_selector)
