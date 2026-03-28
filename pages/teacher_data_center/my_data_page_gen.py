"""Generated Page Object - Do not edit manually"""
from pages.base_page import BasePage, SelectorRecord
from typing import Optional


class MyDataPage(BasePage):
    """我的数据 - 数据应用主环境 page"""

    SELECTORS_HISTORY = {
        "INPUT_": SelectorRecord(
            selector="input[placeholder*='请选择']",
            candidates=["input[placeholder*='请选择']", "input[type='text']"],
            status="untested",
            stability="high"
        ),
        "INPUT_NUMBER": SelectorRecord(
            selector="input[type='number']",
            candidates=["input[type='number']"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_EDIT": SelectorRecord(
            selector="button:has-text('编辑')",
            candidates=["button:has-text('编辑')"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_新增": SelectorRecord(
            selector="button:has-text('新增')",
            candidates=["button:has-text('新增')"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_DELETE": SelectorRecord(
            selector="button:has-text('删除')",
            candidates=["button:has-text('删除')"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_导出": SelectorRecord(
            selector="button#export",
            candidates=['button#export', "button:has-text('导出')"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_自定义列": SelectorRecord(
            selector="button#custom",
            candidates=['button#custom', "button:has-text('自定义列')"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_EDIT": SelectorRecord(
            selector="button#edit",
            candidates=['button#edit', "button:has-text('编辑')"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_DELETE": SelectorRecord(
            selector="button#delete",
            candidates=['button#delete', "button:has-text('删除')"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_审核详情": SelectorRecord(
            selector="button#edit",
            candidates=['button#edit', "button:has-text('审核详情')"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_审核详情": SelectorRecord(
            selector="button#edit",
            candidates=['button#edit', "button:has-text('审核详情')"],
            status="untested",
            stability="medium"
        ),
        "BUTTON_BUTTON": SelectorRecord(
            selector="button:nth-of-type(27)",
            candidates=['button:nth-of-type(27)'],
            status="untested",
            stability="medium"
        ),
        "BUTTON_BUTTON": SelectorRecord(
            selector="button:nth-of-type(28)",
            candidates=['button:nth-of-type(28)'],
            status="untested",
            stability="medium"
        ),
        "A_EDIT": SelectorRecord(
            selector="a#edit",
            candidates=['a#edit', "a:has-text('编辑')"],
            status="untested",
            stability="medium"
        ),
        "A_DELETE": SelectorRecord(
            selector="a#delete",
            candidates=['a#delete', "a:has-text('删除')"],
            status="untested",
            stability="medium"
        ),
        "A_审核详情": SelectorRecord(
            selector="a#edit",
            candidates=['a#edit', "a:has-text('审核详情')"],
            status="untested",
            stability="medium"
        ),
        "A_审核详情": SelectorRecord(
            selector="a#edit",
            candidates=['a#edit', "a:has-text('审核详情')"],
            status="untested",
            stability="medium"
        ),
    }

    # ===== Backward Compatible Selectors =====
    INPUT_ = "input[placeholder*='请选择']"
    INPUT_NUMBER = "input[type='number']"
    BUTTON_EDIT = "button:has-text('编辑')"
    BUTTON_新增 = "button:has-text('新增')"
    BUTTON_DELETE = "button:has-text('删除')"
    BUTTON_导出 = "button#export"
    BUTTON_自定义列 = "button#custom"
    BUTTON_EDIT = "button#edit"
    BUTTON_DELETE = "button#delete"
    BUTTON_审核详情 = "button#edit"
    BUTTON_审核详情 = "button#edit"
    BUTTON_BUTTON = "button:nth-of-type(27)"
    BUTTON_BUTTON = "button:nth-of-type(28)"
    A_EDIT = "a#edit"
    A_DELETE = "a#delete"
    A_审核详情 = "a#edit"
    A_审核详情 = "a#edit"

    # ===== Methods =====
    def submit(self
            value: str,
            value: str,
            ) -> "MyDataPage":
        """Submit form"""
        self.fill("INPUT_", , "")
        self.fill("INPUT_NUMBER", , "")
        return self
