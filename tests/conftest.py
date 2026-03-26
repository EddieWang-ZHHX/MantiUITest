"""
Pytest 配置和 fixtures

支持功能：
- 完整证据收集 (video.webm / trace.zip / screenshot.png / page.html)
- function 级浏览器（每个测试独立 context + 独立视频 + 独立 trace）
- pytest-html 报告（证据超链接）

设计原则：
1. function 级 browser（每个测试独立 context）
2. 证据路径：reports/run_{timestamp}/evidence/{test_name}/
3. pytest-html 报告增强（证据列）
"""

import pytest
import pytest_html
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import Settings
from utils._core.browser_manager import BrowserManager
from utils.logger import logger
from utils._core.test_formatter import TestResult, TestResultFormatter


# ============ 全局状态 ============

_test_evidence = {}
_run_dir = None


# ============ 命令行选项 ============

def pytest_addoption(parser):
    parser.addoption("--output-format", action="store", default="json",
                     choices=["json", "junit", "table", "csv"])
    parser.addoption("--output-file", action="store", default=None)


# ============ Session 生命周期 ============

def pytest_sessionstart(session):
    global _run_dir
    reports_root = project_root / "reports"
    reports_root.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    _run_dir = reports_root / f"run_{ts}"
    _run_dir.mkdir(exist_ok=True)
    logger.info(f"本轮输出目录：{_run_dir}")


# ============ Fixtures ============

@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixture(scope="function")
def browser_manager(settings):
    """每个测试函数使用独立的浏览器实例（function 级）"""
    manager = BrowserManager(settings)
    yield manager
    manager.close()


@pytest.fixture(scope="function")
def page(browser_manager, request):
    """每个测试函数使用独立的 Page"""
    test_name = request.node.name
    browser_manager.start_browser(test_name=test_name)
    browser_manager._rebuild_context()
    return browser_manager.get_page()


@pytest.fixture(scope="session")
def base_url(settings):
    return settings.test.get('base_url', '')


@pytest.fixture(scope="function")
def logged_in_admin(page, base_url):
    import time
    from pages.common.login_page import LoginPage
    lp = LoginPage(page, base_url)
    logger.info("=== 登录（信息中心管理员）===")
    lp.open_login()
    lp.login(username="T100002", password="wisedu@1", verify_code="2222")
    for i in range(5):
        time.sleep(0.5)
        if lp.is_identity_select_visible():
            lp.select_identity_if_needed("信息中心管理员")
            time.sleep(0.5)
            break
        if "login" not in lp.page.url:
            break
    try:
        lp.page.wait_for_url("**/dataapp/**", timeout=10000)
    except:
        pass
    logger.info("=== 登录完成 ===")
    return lp


@pytest.fixture(scope="function")
def logged_in_teacher(page, base_url):
    import time
    from pages.common.login_page import LoginPage
    lp = LoginPage(page, base_url)
    logger.info("=== 登录（教师）===")
    lp.open_login()
    lp.login(username="T100002", password="wisedu@1", verify_code="2222")
    for i in range(8):
        time.sleep(0.5)
        if lp.is_identity_select_visible():
            lp.select_identity_if_needed("教师")
            time.sleep(1)
            break
        if "login" not in lp.page.url and "selectIdentity" not in lp.page.url:
            break
    try:
        lp.page.wait_for_url("**/dataapp/index#/**", timeout=10000)
    except:
        pass
    logger.info("=== 教师登录完成 ===")
    return lp


@pytest.fixture(scope="session")
def my_data_page(page, base_url):
    from pages.teacher_data_center.my_data_page import MyDataPage
    return MyDataPage(page, base_url)


@pytest.fixture(scope="session")
def data_query_page(page, base_url):
    from pages.teacher_data_center.teacher_data_query_page import TeacherDataQueryPage
    return TeacherDataQueryPage(page, base_url)


@pytest.fixture(scope="session")
def create_page(page, base_url):
    def _create(page_name: str):
        from pages import get_page
        return get_page(page_name)(page, base_url)
    return _create


# ============ 证据工具 ============

def _format_path_as_url(path: Path) -> str:
    abs_path = path.absolute()
    return f"file:///{str(abs_path).replace(chr(92), '/')}"


def _get_evidence_for_test(test_name: str) -> dict:
    evidence_dir = Path("reports/evidence") / test_name
    if not evidence_dir.exists():
        return {}
    evidence = {}
    for f in evidence_dir.iterdir():
        if f.suffix == ".png" and "screenshot" in f.name.lower():
            evidence["screenshot"] = f
        elif f.suffix == ".webm" and f.name == "video.webm":
            evidence["video"] = f
        elif f.suffix == ".zip" and "trace" in f.name.lower():
            evidence["trace"] = f
        elif f.name == "page.html":
            evidence["page"] = f
    return evidence


def _create_evidence_html(test_name: str, is_failed: bool = False) -> str:
    evidence = _get_evidence_for_test(test_name)
    if not evidence:
        return ""
    links = []
    icons = {"screenshot": "📷", "video": "🎬", "trace": "🔍", "page": "📄"}
    order = ["video"] if not is_failed else ["screenshot", "video", "trace", "page"]
    for key in order:
        if key not in evidence:
            continue
        fp = evidence[key]
        url = _format_path_as_url(fp)
        links.append(f'<a href="{url}" target="_blank">{icons.get(key,"📎")} {key.upper()}</a>')
    return '<div class="evidence-links">' + ''.join(links) + '</div>'


# ============ pytest-runtest-makereport ============

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        test_name = item.name
        is_failed = report.passed is False
        test_status = "failed" if is_failed else "passed"

        # 保存证据
        try:
            if 'browser_manager' in item.funcargs:
                bm = item.funcargs['browser_manager']
                if bm:
                    bm.save_evidence(test_status, test_name=test_name)
                    logger.info(f"证据已保存 [{test_name}]，状态：{test_status}")
        except Exception as e:
            logger.error(f"保存证据失败：{e}")

        # 生成证据 HTML
        evidence_html = _create_evidence_html(test_name, is_failed)
        _test_evidence[test_name] = evidence_html

        # 添加到 pytest-html 报告（正确的 extra 方式）
        if evidence_html:
            report.extras = getattr(report, 'extras', [])
            report.extras.append(pytest_html.extras.html(evidence_html))

        if is_failed:
            logger.error(f"❌ {test_name}: {report.longreprtext}")
        else:
            logger.info(f"✅ {test_name}")


# ============ pytest-html 报告增强 ============

def pytest_html_results_table_header(cells):
    cells.insert(2, '<th class="col-evidence">证据</th>')


def pytest_html_results_table_row(report, cells):
    test_name = report.nodeid.split("::")[-1].split("[")[0]
    evidence_html = _test_evidence.get(test_name, '<span style="color:#999;">-</span>')
    cells.insert(2, f'<td class="col-evidence">{evidence_html}</td>')


# ============ pytest_terminal_summary ============

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    terminalreporter.write_line("")
    terminalreporter.write_line("=" * 70)
    terminalreporter.write_line(f"📊 测试报告：C:\\11_UITest\\reports\\report.html")
    terminalreporter.write_line("=" * 70)
