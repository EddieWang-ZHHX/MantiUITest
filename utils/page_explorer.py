import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from utils.parsers import ParserFactory, PageSnapshot, ElementInfo
from utils.cache_manager import CacheManager
from utils.session_cache import SessionCache
from utils.evolution.decorator import evolution_monitor


class PageExplorer:
    """
    Page Explorer - AI 专用工具

    工作流:
    1. explore() → 分析结果 + Markdown 报告
    2. 人审计 Markdown 报告
    3. generate_pom() → POM 代码
    """

    def __init__(self, parser_type: str = "playwright"):
        self.parser = ParserFactory.create(parser_type)
        self.cache = CacheManager()
        self.session_cache = SessionCache()
        self._current_context = None

    @evolution_monitor("page_explorer.login")
    def login(
        self,
        url: str,
        username: str,
        password: str,
        verify_code: str = "2222",
        identity: str = None,
        session_name: str = "default",
        force: bool = False,
    ) -> bool:
        """
        执行登录并缓存 Session

        Returns:
            bool: 登录是否成功
        """
        from playwright.sync_api import sync_playwright
        from pages.common.login_page import LoginPage

        if not force and self.session_cache.exists(session_name):
            session = self.session_cache.load(session_name)
            if session:
                return True

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True,
            )
            page = context.new_page()

            # 使用 LoginPage 类进行登录（复用现有逻辑）
            base_url = url.replace("/login", "")
            login_page = LoginPage(page, base_url)
            
            # 打开登录页面
            login_page.open_login()
            
            # 执行登录
            login_page.login(
                username=username,
                password=password,
                verify_code=verify_code,
                identity=identity
            )
            
            # 检查是否登录成功
            if not login_page.is_logged_in():
                return False

            cookies = context.cookies()

            try:
                local_storage = page.evaluate("() => JSON.stringify(localStorage)")
                local_storage = json.loads(local_storage) if local_storage else {}
            except:
                local_storage = {}

            try:
                session_storage = page.evaluate("() => JSON.stringify(sessionStorage)")
                session_storage = json.loads(session_storage) if session_storage else {}
            except:
                session_storage = {}

            self.session_cache.save(
                session_name=session_name,
                cookies=cookies,
                local_storage=local_storage,
                session_storage=session_storage,
                login_url=url,
                username=username,
                identity=identity or "",
            )

            self._current_context = context
            return True

    def _fill_login_form(self, page, username: str, password: str, verify_code: str):
        try:
            page.locator("input[placeholder*='用户名']").fill(username)
        except:
            page.locator("input[name='username']").fill(username)

        try:
            page.locator("input[placeholder*='密码']").fill(password)
        except:
            page.locator("input[name='password']").fill(password)

        try:
            page.locator("input[placeholder*='验证码']").fill(verify_code)
        except:
            pass

    def _select_identity(self, page, identity: str):
        try:
            page.wait_for_selector("text=您有多身份", timeout=3000)
            page.locator(f"text={identity}").click()
            page.wait_for_timeout(1000)
        except:
            pass

    @evolution_monitor("page_explorer.explore")
    def explore(
        self,
        url: str,
        module: str,
        page_name: str,
        force: bool = False,
        session_name: str = "default",
        auto_login: bool = True,
    ) -> Dict[str, Any]:
        """
        探索页面

        Args:
            url: 页面 URL
            module: 业务模块
            page_name: 页面名称
            force: 是否强制重新探索
            session_name: Session 名称
            auto_login: 缓存过期时是否自动重新登录

        Returns:
            dict: {
                "snapshot": PageSnapshot,
                "report_path": str,
                "cache_path": str,
                "from_cache": bool
            }
        """
        from playwright.sync_api import sync_playwright

        session = self.session_cache.load(session_name) if session_name else None

        snapshot = None
        context = None

        if session and not force:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=False)
                    context = browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        ignore_https_errors=True,
                    )
                    context.add_cookies(session.cookies)
                    page = context.new_page()
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=30000)

                    snapshot = self.parser.parse(url, context=context)
                    browser.close()
            except Exception as e:
                snapshot = None

        if not snapshot:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    ignore_https_errors=True,
                )
                if session:
                    try:
                        context.add_cookies(session.cookies)
                    except:
                        pass

                page = context.new_page()
                page.goto(url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=30000)

                snapshot = self.parser.parse(url, context=context)
                browser.close()

        cache_path = self.cache.save_snapshot(module, page_name, snapshot)
        report_path = self._generate_report(snapshot, module, page_name)

        return {
            "snapshot": snapshot.to_dict(),
            "report_path": str(report_path),
            "cache_path": str(cache_path),
            "from_cache": False,
        }

    def explore_offline(
        self, html_file: str, module: str, page_name: str
    ) -> Dict[str, Any]:
        """离线探索 (使用 HTML 解析器)"""
        raise NotImplementedError("HTML parser not implemented yet")

    def get_cached(self, module: str, page_name: str) -> Optional[Dict]:
        """获取缓存的探索结果"""
        return self.cache.load_raw(module, page_name)

    def get_report_path(self, module: str, page_name: str) -> str:
        """获取 Markdown 报告路径"""
        return str(self.cache._get_path(module, page_name, "md"))

    @evolution_monitor("page_explorer.generate_pom")
    def generate_pom(self, snapshot: Dict, module: str, page_name: str) -> str:
        """基于分析结果生成 POM 代码"""
        from utils.parsers.base_parser import PageSnapshot, ElementInfo

        if isinstance(snapshot, dict):
            snapshot = PageSnapshot.from_dict(snapshot)

        class_name = self._to_class_name(page_name)

        lines = [
            '"""Generated Page Object - Do not edit manually"""',
            f"from pages.base_page import BasePage, SelectorRecord",
            f"from typing import Optional",
            f"",
            f"",
            f"class {class_name}(BasePage):",
            f'    """{snapshot.title or page_name} page"""',
            f"",
            f"    SELECTORS_HISTORY = {{",
        ]

        for element in snapshot.elements:
            selector_name = self._to_selector_name(element)
            selector_value = element.selector
            candidates = (
                element.selector_candidates
                if element.selector_candidates
                else [selector_value]
            )
            stability = self._to_stability(element)

            lines.append(f'        "{selector_name}": SelectorRecord(')
            lines.append(f'            selector="{selector_value}",')
            lines.append(f"            candidates={candidates},")
            lines.append(f'            status="untested",')
            lines.append(f'            stability="{stability}"')
            lines.append(f"        ),")

        lines.append("    }")
        lines.append("")
        lines.append("    # ===== Backward Compatible Selectors =====")
        for element in snapshot.elements:
            selector_name = self._to_selector_name(element)
            selector_value = element.selector
            lines.append(f'    {selector_name} = "{selector_value}"')

        lines.append("")
        lines.append("    # ===== Methods =====")

        input_fields = [e for e in snapshot.elements if e.group == "inputs"]

        if input_fields:
            lines.append(f"    def submit(self")

            params = []
            for elem in input_fields:
                ph = elem.attrs.get("placeholder", "").lower()
                if "用户名" in ph or "用户" in ph:
                    params.append("username: str")
                elif "密码" in ph:
                    params.append("password: str")
                elif "验证码" in ph:
                    params.append("verify_code: str = '2222'")
                elif "手机" in ph:
                    params.append("phone: str")
                elif "邮箱" in ph:
                    params.append("email: str")
                else:
                    params.append("value: str")

            for param in params:
                lines.append(f"            {param},")

            lines.append(f'            ) -> "{class_name}":')
            lines.append(f'        """Submit form"""')

            for elem, param in zip(input_fields, params):
                var_name = param.split(":")[0].strip()
                if var_name == "value":
                    var_name = self._to_var_name(elem.attrs.get("placeholder", ""))
                selector_name = self._to_selector_name(elem)
                lines.append(
                    f'        self.fill("{selector_name}", {var_name}, "{var_name}")'
                )

            lines.append(f"        return self")
        else:
            lines.append(f'    def some_action(self) -> "{class_name}":')
            lines.append(f'        """TODO: Add action logic"""')
            lines.append(f"        pass")
            lines.append(f"        return self")

        lines.append("")

        return "\n".join(lines)

    def _generate_report(
        self, snapshot: PageSnapshot, module: str, page_name: str
    ) -> Path:
        lines = [
            f"# {snapshot.title or page_name} Analysis",
            "",
            "## Page Info",
            f"- **URL**: {snapshot.url}",
            f"- **Title**: {snapshot.title or 'N/A'}",
            f"- **Explored**: {snapshot.explored_at}",
            f"- **Parser**: {snapshot.parser}",
            "",
            "## Summary",
            f"- Total elements: {len(snapshot.elements)}",
            f"- Forms: {len(snapshot.forms)}",
            f"- Buttons: {len(snapshot.buttons)}",
            f"- Links: {len(snapshot.links)}",
            f"- Inputs: {len(snapshot.inputs)}",
            "",
            "## Elements",
            "",
            "| # | Tag | Selector | Placeholder | Text | Stability |",
            "|---|-----|----------|-------------|------|-----------|",
        ]

        for idx, elem in enumerate(snapshot.elements, 1):
            placeholder = elem.attrs.get("placeholder", "-")
            text = elem.text[:30] if elem.text else "-"
            stability = elem.stability.upper()
            lines.append(
                f"| {idx} | {elem.tag} | `{elem.selector}` | {placeholder} | {text} | {stability} |"
            )

        lines.append("")
        lines.append("## Selector Candidates")
        lines.append("")

        for elem in snapshot.elements:
            if elem.selector_candidates:
                lines.append(
                    f"### {elem.tag} - {elem.attrs.get('placeholder', elem.text[:20])}"
                )
                for i, cand in enumerate(elem.selector_candidates, 1):
                    marker = " (primary)" if i == 1 else ""
                    lines.append(f"- `{cand}`{marker}")
                lines.append("")

        if snapshot.forms:
            lines.append("## Forms")
            for form in snapshot.forms:
                lines.append(f"### {form.name}")
                for eid in form.element_ids:
                    for elem in snapshot.elements:
                        if elem.element_id == eid:
                            selector_name = self._to_selector_name(elem)
                            lines.append(f"- {selector_name}: `{elem.selector}`")
                lines.append("")

        if snapshot.buttons:
            lines.append("## Buttons")
            for btn in snapshot.buttons:
                selector_name = self._to_selector_name(btn)
                lines.append(f"- {selector_name}: `{btn.selector}`")
            lines.append("")

        lines.append("---")
        lines.append("<!-- Human audit zone: Edit above to correct/add elements -->")

        content = "\n".join(lines)

        path = self.cache._get_path(module, page_name, "md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        return path

    def _to_class_name(self, page_name: str) -> str:
        parts = page_name.replace("-", "_").replace("_page", "").split("_")
        return "".join(p.capitalize() for p in parts if p) + "Page"

    def _to_selector_name(self, element: ElementInfo) -> str:
        placeholder = element.attrs.get("placeholder", "")
        name = element.attrs.get("name", "")
        text = element.text
        input_type = element.attrs.get("type", "")

        key = ""
        if placeholder:
            p = placeholder.lower()
            if "用户名" in placeholder or "用户" in p:
                key = "USERNAME"
            elif "密码" in p:
                key = "PASSWORD"
            elif "验证码" in p or "code" in p:
                key = "VERIFY_CODE"
            elif "手机" in p or "tel" in p:
                key = "PHONE"
            elif "邮箱" in p or "email" in p:
                key = "EMAIL"
            else:
                key = self._translate_to_english(placeholder)
        elif name:
            key = name.upper()
        elif text:
            key = self._text_to_key(text)
        elif input_type:
            key = input_type.upper()
        else:
            key = f"{element.tag.upper()}_{element.element_id}"

        tag_upper = element.tag.upper()
        return f"{tag_upper}_{key}"

    def _translate_to_english(self, text: str) -> str:
        text = text.replace("请输入", "").replace("请选择", "").replace("请", "")
        text = text.strip()
        text = text.replace(" ", "_")
        if len(text) > 20:
            text = text[:20]
        return text.upper()

    def _text_to_key(self, text: str) -> str:
        text = text.strip()[:30]
        text = text.replace(" ", "_")

        chinese_map = {
            "登录": "LOGIN",
            "忘记密码": "FORGOT_PASSWORD",
            "注册": "REGISTER",
            "提交": "SUBMIT",
            "取消": "CANCEL",
            "保存": "SAVE",
            "删除": "DELETE",
            "编辑": "EDIT",
            "关闭": "CLOSE",
            "确定": "CONFIRM",
            "下一步": "NEXT",
            "上一步": "PREV",
            "返回": "BACK",
            "搜索": "SEARCH",
            "查询": "QUERY",
            "重置": "RESET",
            "选择": "SELECT",
            "确认": "CONFIRM",
        }

        for cn, en in chinese_map.items():
            if cn in text:
                text = text.replace(cn, en)

        return text.upper()

    def _to_method_name(self, name: str) -> str:
        return name.replace("-", "_").replace(" ", "_")

    def _to_var_name(self, text: str) -> str:
        text = text.replace("请输入", "").replace("请选择", "").replace("请", "")
        text = text.strip()
        text = text.replace(" ", "_")

        if "用户名" in text or "用户" in text.lower():
            return "username"
        elif "密码" in text:
            return "password"
        elif "验证码" in text:
            return "verify_code"
        elif "手机" in text:
            return "phone"
        elif "邮箱" in text or "邮件" in text:
            return "email"

        return text.lower()

    def _to_stability(self, element: ElementInfo) -> str:
        """根据选择器类型判断稳定性"""
        if element.stability:
            return element.stability

        selector = element.selector.lower()

        if "[placeholder" in selector or "[aria-label" in selector:
            return "high"
        elif "[name" in selector or "[id=" in selector:
            return "medium"
        elif ":nth-of-type" in selector or ":nth-child" in selector:
            return "low"

        return "medium"

    def close(self):
        if self._current_context:
            try:
                self._current_context.close()
            except:
                pass
