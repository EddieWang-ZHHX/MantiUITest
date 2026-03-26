"""
Pytest 配置和 fixtures

支持功能：
- 完整证据收集 (视频、截图、HTML、Trace)
- 页面对象自动发现
- 多格式输出 (JSON, JUnit XML, Table)
- CI/CD 友好 (并行执行、无状态)
- pytest-html 报告增强（证据超链接）

设计原则：
1. 每个测试函数使用独立的浏览器实例 (scope="function")
2. 无状态设计，可重复执行
3. 支持 pytest-xdist 并行执行
4. 输出 JUnit XML 格式供 CI/CD 使用
"""

import pytest
import pytest_html
import os
import sys
from pathlib import Path
from datetime import datetime

# 确保项目根目录在 path 中
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import Settings
from utils.browser_manager import BrowserManager
from utils.logger import logger
from utils.test_formatter import TestResult, TestResultFormatter


# ============ 全局配置 ============

def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--output-format",
        action="store",
        default="json",
        choices=["json", "junit", "table", "csv"],
        help="测试结果输出格式 (默认: json)"
    )
    parser.addoption(
        "--output-file",
        action="store",
        default=None,
        help="测试结果输出文件路径"
    )


# ============ Fixtures ============

@pytest.fixture(scope="session")
def settings():
    """获取配置 (session 级，整个测试会话共享)"""
    return Settings()


@pytest.fixture(scope="function")
def browser_manager(settings, request):
    """浏览器管理器 fixture
    
    每个测试函数使用独立的浏览器实例
    scope="function" 确保测试隔离
    """
    manager = BrowserManager(settings)
    yield manager
    manager.close()


@pytest.fixture(scope="function")
def page(browser_manager, request):
    """获取页面实例
    
    每个测试使用独立的浏览器页面
    """
    test_name = request.node.name
    browser_manager.start_browser(test_name=test_name)
    page = browser_manager.get_page()
    yield page


@pytest.fixture(scope="function")
def base_url(settings):
    """获取基础 URL"""
    return settings.test.get('base_url', '')


# ============ 登录相关 fixtures ============

@pytest.fixture(scope="function")
def login_page(page, base_url):
    """登录页面对象"""
    from pages.common.login_page import LoginPage
    login_page = LoginPage(page, base_url)
    yield login_page


@pytest.fixture(scope="function")
def logged_in_user(login_page):
    """已登录用户 fixture（自动登录）
    
    自动完成登录流程
    注意：需要确保测试环境网络稳定
    """
    logger.info("自动登录...")
    login_page.open_login()
    login_page.login(
        username="T100002",
        password="wisedu@1",
        verify_code="2222"
    )
    
    # 等待登录成功
    if not login_page.is_logged_in():
        pytest.fail("登录失败，请检查网络和账号状态")
    
    yield login_page


@pytest.fixture(scope="function")
def logged_in_admin(login_page):
    """已登录的管理员身份 fixture"""
    import time
    logger.info("自动登录（管理员身份）...")
    login_page.open_login()
    login_page.login(
        username="T100002",
        password="wisedu@1",
        verify_code="2222"
    )
    for i in range(8):
        time.sleep(0.5)
        if login_page.is_identity_select_visible():
            login_page.select_identity_if_needed("信息中心管理员")
            time.sleep(0.5)
            break
        if "login" not in login_page.page.url:
            break
    if not login_page.is_logged_in():
        pytest.fail("登录失败")
    yield login_page


# ============ 教师数据中心 fixtures ============

@pytest.fixture(scope="function")
def my_data_page(page, base_url):
    """我的数据页面对象"""
    from pages.teacher_data_center.my_data_page import MyDataPage
    my_data_page = MyDataPage(page, base_url)
    yield my_data_page


# ============ 页面对象动态获取 ============

@pytest.fixture(scope="function")
def create_page(page, base_url, request):
    """动态创建页面对象的工厂函数
    
    使用方式:
        def test_something(create_page):
            login = create_page("login")
            login.navigate_to()
            
            my_data = create_page("my_data")
            my_data.navigate_to()
    
    CI/CD 优势: 减少 fixture 数量，按需创建
    """
    created_pages = []
    
    def _create(page_name: str):
        from pages import get_page
        page_class = get_page(page_name)
        page_obj = page_class(page, base_url)
        created_pages.append(page_obj)
        return page_obj
    
    yield _create
    
    # 清理 (如果页面对象有 cleanup 方法)
    for page_obj in created_pages:
        if hasattr(page_obj, 'cleanup'):
            try:
                page_obj.cleanup()
            except:
                pass


# ============ 测试结果收集 (CI/CD) ============

# 全局测试结果列表
_test_results = []


def get_test_results():
    """获取测试结果列表"""
    return _test_results


def _format_path_as_url(path: Path) -> str:
    """将路径转换为 file:// URL 格式"""
    abs_path = path.absolute()
    return f"file:///{str(abs_path).replace(chr(92), '/')}"


def _get_evidence_for_test(test_name: str) -> dict:
    """获取测试的证据文件信息"""
    evidence_dir = project_root / "reports" / "evidence" / test_name
    
    if not evidence_dir.exists():
        return {}
    
    evidence = {}
    for f in evidence_dir.iterdir():
        if "screenshot" in f.name.lower() and f.suffix == ".png":
            # 优先使用不带 _failed 后缀的截图
            if "screenshot.png" == f.name:
                evidence["screenshot"] = f
            elif "screenshot" in evidence:
                pass  # 已存在，不覆盖
            else:
                evidence["screenshot"] = f
        elif "video" in f.name.lower() and f.suffix == ".webm":
            # 优先使用固定的 video.webm
            if f.name == "video.webm":
                evidence["video"] = f
            elif "video" not in evidence:
                evidence["video"] = f
        elif "trace" in f.name.lower() and f.suffix == ".zip":
            evidence["trace"] = f
        elif f.name == "page.html":
            evidence["page"] = f
        elif "console" in f.name.lower() and f.suffix == ".log":
            evidence["console"] = f
    
    return evidence


def _create_evidence_html(test_name: str, is_failed: bool = False) -> str:
    """创建证据链接的 HTML 代码
    
    Args:
        test_name: 测试名称
        is_failed: 是否失败测试（失败时显示所有证据，通过时只显示视频）
    """
    evidence = _get_evidence_for_test(test_name)
    
    if not evidence:
        return ""
    
    links = []
    
    icons = {
        "screenshot": "📷",
        "video": "🎬",
        "trace": "🔍",
        "page": "📄",
        "console": "📝"
    }
    
    # 失败测试显示所有证据，通过测试只显示视频
    evidence_order = ["video"] if not is_failed else ["screenshot", "video", "trace", "page"]
    
    for evidence_type in evidence_order:
        if evidence_type not in evidence:
            continue
        
        file_path = evidence[evidence_type]
        url = _format_path_as_url(file_path)
        
        icon = icons.get(evidence_type, "📎")
        label = evidence_type.upper()
        links.append(f'<a href="{url}" target="_blank">{icon} {label}</a>')
    
    return '<div class="evidence-links">' + ''.join(links) + '</div>'


def _log_evidence_links(test_name: str, evidence_paths: dict):
    """输出证据链接到日志"""
    evidence_dir = Path("reports/evidence") / test_name
    evidence_dir_abs = evidence_dir.absolute()
    
    logger.error(f"📁 证据目录：{_format_path_as_url(evidence_dir_abs)}")
    
    file_icons = {
        "screenshot": "📷",
        "video": "🎬",
        "trace": "🔍",
        "page": "📄"
    }
    
    for key, path in evidence_paths.items():
        if path and Path(path).exists():
            icon = file_icons.get(key, "📎")
            logger.error(f"  {icon} {key.upper()}: {_format_path_as_url(Path(path))}")
        elif path:
            logger.error(f"  📎 {key.upper()}: {path} (文件不存在)")


# ============ Pytest-HTML 报告增强 ============

# 存储每个测试的证据信息
_test_evidence = {}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """收集测试结果并保存证据"""
    outcome = yield
    report = outcome.get_result()
    
    # 收集测试结果
    if report.when == 'call':
        result = TestResult(
            name=item.name,
            status="passed" if report.passed else "failed",
            duration=call.stop - call.start if hasattr(call, 'stop') and call.stop else 0.0,
            message=str(call.excinfo) if call.excinfo else None,
            test_class=item.nodeid.split("::")[1] if "::" in item.nodeid else None,
        )
        _test_results.append(result)
        
        # 保存证据
        evidence_paths = {}
        try:
            if 'browser_manager' in item.funcargs:
                browser_manager = item.funcargs['browser_manager']
                test_status = "passed" if report.passed else "failed"
                evidence_paths = browser_manager.save_evidence(test_status)
            
            if report.passed:
                logger.info(f"✅ 测试通过：{item.name}")
            elif report.failed:
                logger.error(f"❌ 测试失败：{item.name}")
                logger.error(f"错误信息：{report.longreprtext}")
                _log_evidence_links(item.name, evidence_paths)
        except Exception as e:
            logger.error(f"处理测试结果时出错：{e}")
        
        # 为 pytest-html 存储证据信息
        test_name = item.name
        is_failed = report.passed is False
        evidence_html = _create_evidence_html(test_name, is_failed)
        _test_evidence[test_name] = evidence_html
        
        # 添加到报告的 extra 列表（这是正确的方式）
        if evidence_html:
            report.extra = getattr(report, 'extra', [])
            report.extra.append(pytest_html.extras.html(evidence_html))


def pytest_html_results_table_header(cells):
    """添加"证据"列到报告表头"""
    cells.insert(2, '<th class="col-evidence">证据</th>')


def pytest_html_results_table_row(report, cells):
    """在每行添加证据链接"""
    # 从 nodeid 提取测试名称
    test_name = report.nodeid.split("::")[-1].split("[")[0]
    evidence_html = _test_evidence.get(test_name, '<span style="color: #999;">-</span>')
    cells.insert(2, f'<td class="col-evidence">{evidence_html}</td>')


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """测试结束后的摘要报告
    
    支持多种输出格式
    """
    results = get_test_results()
    if not results:
        return
    
    output_format = config.getoption("--output-format", "json")
    output_file = config.getoption("--output-file", None)
    
    # 生成报告
    if output_format == "json":
        output = TestResultFormatter.to_json(results, pretty=True)
    elif output_format == "junit":
        output = TestResultFormatter.to_junit_xml(results)
    elif output_format == "table":
        output = TestResultFormatter.to_table(results)
    elif output_format == "csv":
        output = TestResultFormatter.to_csv(results)
    else:
        output = TestResultFormatter.to_json(results)
    
    # 输出到文件
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding='utf-8')
        terminalreporter.write_line(f"\n测试结果已保存: {output_path.absolute()}")
    
    # 输出到控制台 (非 CI 环境)
    if output_format == "table" or os.environ.get("CI") is None:
        terminalreporter.write_line("\n" + "=" * 70)
        terminalreporter.write_line("测试摘要:")
        terminalreporter.write_line(TestResultFormatter.to_table(results))
        terminalreporter.write_line("=" * 70)
    
    # 在 CI 环境中额外输出 JUnit XML 到默认位置
    if os.environ.get("CI") == "true" and output_format != "junit":
        junit_output = Path("reports/test-results.xml")
        junit_output.parent.mkdir(parents=True, exist_ok=True)
        junit_output.write_text(TestResultFormatter.to_junit_xml(results), encoding='utf-8')
