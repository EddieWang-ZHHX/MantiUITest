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
    # 从测试文件路径提取模块名：如 tests/teacher_data_center/test_my_data.py → teacher_data_center
    test_file = str(request.node.fspath)
    parts = Path(test_file).parts
    if "teacher_data_center" in parts:
        module = "teacher_data_center"
    elif "common" in parts:
        module = "common"
    else:
        module = "common"
    browser_manager.start_browser(test_name=test_name, module=module)
    page = browser_manager.get_page()
    yield page


@pytest.fixture(scope="function")
def base_url(settings):
    """获取基础 URL"""
    return settings.base_url


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
    """将路径转换为相对路径（相对于 reports/ 目录）
    
    报告在 reports/report.html，证据在 reports/evidence/{test}/，相对路径如 evidence/{test}/video.webm
    """
    try:
        rel_path = path.relative_to(project_root / "reports")
        return str(rel_path).replace(chr(92), '/')
    except ValueError:
        # fallback 到绝对路径
        abs_path = path.absolute()
        return f"file:///{str(abs_path).replace(chr(92), '/')}"


def _get_evidence_for_test(test_name: str) -> dict:
    """获取测试的证据文件信息
    
    支持两种目录结构：
    1. 新结构: reports/evidence/{module}/{test_name}/
    2. 旧结构: reports/evidence/{test_name}/
    """
    # 新结构（带模块层级）
    evidence_dir_new = project_root / "reports" / "evidence"
    if evidence_dir_new.exists():
        for module_dir in evidence_dir_new.iterdir():
            if module_dir.is_dir():
                evidence_dir = module_dir / test_name
                if evidence_dir.exists():
                    return _scan_evidence_dir(evidence_dir)
    
    # 旧结构（扁平）
    evidence_dir = project_root / "reports" / "evidence" / test_name
    if evidence_dir.exists():
        return _scan_evidence_dir(evidence_dir)
    
    return {}


def _scan_evidence_dir(evidence_dir: Path) -> dict:
    """扫描证据目录，返回文件字典"""
    evidence = {}
    for f in evidence_dir.iterdir():
        if f.is_file():
            if "screenshot" in f.name.lower() and f.suffix == ".png":
                if "screenshot.png" == f.name:
                    evidence["screenshot"] = f
                elif "screenshot" not in evidence:
                    evidence["screenshot"] = f
            elif "video" in f.name.lower() and f.suffix == ".webm":
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


def _create_evidence_html_direct(test_name: str, module: str, is_failed: bool) -> str:
    """直接从证据目录扫描文件生成 HTML
    
    Args:
        test_name: 测试名称
        module: 模块名
        is_failed: 是否失败测试
    """
    # 优先在新结构查找：reports/evidence/{module}/{test_name}/
    evidence_dir = project_root / "reports" / "evidence" / module / test_name
    
    # 回退旧结构：reports/evidence/{test_name}/
    if not evidence_dir.exists():
        evidence_dir = project_root / "reports" / "evidence" / test_name
    
    if not evidence_dir.exists():
        return '<span style="color: #999;">-</span>'
    
    evidence = _scan_evidence_dir(evidence_dir)
    if not evidence:
        return '<span style="color: #999;">-</span>'
    
    icons = {
        "screenshot": "📷",
        "video": "🎬",
        "trace": "🔍",
        "page": "📄",
        "console": "📝"
    }
    
    # 失败测试显示所有证据，通过测试只显示视频
    evidence_order = ["video"] if not is_failed else ["screenshot", "video", "trace", "page"]
    
    links = []
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
        # 从测试文件路径提取模块名
        test_file = str(item.fspath)
        parts = Path(test_file).parts
        if "teacher_data_center" in parts:
            module = "teacher_data_center"
        elif "common" in parts:
            module = "common"
        else:
            module = "common"
        
        result = TestResult(
            name=item.name,
            status="passed" if report.passed else "failed",
            duration=call.stop - call.start if hasattr(call, 'stop') and call.stop else 0.0,
            message=str(call.excinfo) if call.excinfo else None,
            test_class=module,
            nodeid=item.nodeid,
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
        module = _get_module_from_nodeid(item.nodeid)
        is_failed = report.passed is False
        evidence_html = _create_evidence_html(test_name, is_failed)
        # 用模块前缀的 key 存储，这样查找时能匹配上
        _test_evidence[f"{module}::{test_name}"] = evidence_html
        
        # 添加到报告的 extra 列表（这是正确的方式）
        if evidence_html:
            report.extra = getattr(report, 'extra', [])
            report.extra.append(pytest_html.extras.html(evidence_html))


def pytest_html_results_table_header(cells):
    """添加"证据"列和"源码"列到报告表头"""
    cells.insert(2, '<th class="col-evidence">证据</th>')
    cells.insert(3, '<th class="col-source">源码</th>')


def pytest_html_results_summary(prefix, summary, postfix, session):
    """在 HTML 报告顶部添加分组摘要"""
    results = get_test_results()
    if not results:
        return
    
    # 构建模块分组
    modules = {}
    for r in results:
        m = r.test_class or "common"
        if m not in modules:
            modules[m] = {"passed": 0, "failed": 0, "tests": []}
        if r.status == "passed":
            modules[m]["passed"] += 1
        else:
            modules[m]["failed"] += 1
        modules[m]["tests"].append(r)
    
    # 整体统计
    total_passed = sum(1 for r in results if r.status == "passed")
    total_failed = sum(1 for r in results if r.status == "failed")
    total_dur = sum(r.duration for r in results)
    
    # 生成 HTML
    module_rows = []
    for module, data in sorted(modules.items()):
        icon = "✅" if data["failed"] == 0 else "❌"
        status_cls = "module-ok" if data["failed"] == 0 else "module-fail"
        test_details = " | ".join(
            f"{'✅' if t.status == 'passed' else '❌'} {t.name} ({t.duration:.1f}s)"
            for t in data["tests"]
        )
        module_rows.append(
            f'<tr class="{status_cls}">'
            f'<td>{icon} {module}</td>'
            f'<td>{data["passed"]} passed, {data["failed"]} failed</td>'
            f'<td>{test_details}</td>'
            f'</tr>'
        )
    
    html = f"""
    <style>
        .report-summary {{ margin: 15px 0; }}
        .report-summary h2 {{ margin: 0 0 10px 0; font-size: 15px; }}
        .report-summary table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        .report-summary th {{ text-align: left; padding: 6px 10px; background: #f0f0f0; }}
        .report-summary td {{ padding: 6px 10px; border-bottom: 1px solid #eee; }}
        .module-ok td:first-child {{ color: #2e7d32; }}
        .module-fail td:first-child {{ color: #c62828; }}
    </style>
    <div class="report-summary">
        <h2>📊 测试结果摘要</h2>
        <table>
            <thead>
                <tr><th>模块</th><th>统计</th><th>测试详情</th></tr>
            </thead>
            <tbody>
                {"".join(module_rows)}
            </tbody>
        </table>
        <p style="margin:10px 0 0 0;font-weight:bold;">📊 合计: {total_passed} passed, {total_failed} failed | 总耗时: {total_dur:.1f}s</p>
    </div>
    """
    summary.append(html)


def _get_module_from_nodeid(nodeid: str) -> str:
    """从 nodeid 提取模块名
    
    基于目录结构判断：tests/{模块}/test_xxx.py
    """
    # 从文件路径提取模块目录
    # nodeid: tests/common/test_00_login.py::TestLogin::test_login_success
    test_file = nodeid.split("::")[0]  # tests/common/test_00_login.py
    parts = Path(test_file).parts
    if "teacher_data_center" in parts:
        return "teacher_data_center"
    elif "common" in parts:
        return "common"
    else:
        return "common"


def pytest_html_results_table_row(report, cells):
    """在每行添加证据链接，测试名称加模块前缀
    
    直接从证据目录扫描文件生成 HTML，不依赖缓存
    """
    nodeid = report.nodeid
    test_name = nodeid.split("::")[-1].split("[")[0]
    module = _get_module_from_nodeid(nodeid)
    is_failed = report.passed is False
    
    # 修改测试ID列，加上模块前缀
    for i, cell in enumerate(cells):
        if 'col-testId' in cell and nodeid in cell:
            new_cell = cell.replace(
                nodeid,
                f'<span class="module-tag">{module}</span> / {nodeid}'
            )
            cells[i] = new_cell
            break
    
    # 直接从证据目录扫描，生成 HTML
    evidence_html = _create_evidence_html_direct(test_name, module, is_failed)
    cells.insert(2, f'<td class="col-evidence">{evidence_html}</td>')
    
    # 添加源码列（链接到测试文件）
    # 报告在 reports/report.html，测试文件在 tests/{模块}/ 下
    # nodeid 如：tests/common/test_00_login.py::TestLogin::test_login_success
    # 相对路径：../../tests/common/test_00_login.py
    test_file = nodeid.split("::")[0]  # tests/common/test_00_login.py
    source_link = f'<a href="../../{test_file}" target="_blank">📄 源码</a>'
    cells.insert(3, f'<td class="col-source">{source_link}</td>')


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """测试结束后的摘要报告
    
    支持多种输出格式，包含整体 + 分组统计
    """
    results = get_test_results()
    if not results:
        return
    
    # 构建模块分组
    modules = {}
    for r in results:
        m = r.test_class or "common"
        if m not in modules:
            modules[m] = []
        modules[m].append(r)
    
    # 按模块分组输出
    terminalreporter.write_line("")
    terminalreporter.write_line("=" * 70)
    terminalreporter.write_line("📦 分模块测试结果:")
    terminalreporter.write_line("-" * 70)
    
    for module, mod_results in sorted(modules.items()):
        passed = sum(1 for r in mod_results if r.status == "passed")
        failed = sum(1 for r in mod_results if r.status == "failed")
        total = len(mod_results)
        total_dur = sum(r.duration for r in mod_results)
        status_icon = "✅" if failed == 0 else "❌"
        terminalreporter.write_line(
            f"  {status_icon} [{module}] {passed} passed, {failed} failed ({total_dur:.1f}s)"
        )
        for r in mod_results:
            icon = "✅" if r.status == "passed" else "❌"
            terminalreporter.write_line(f"      {icon} {r.name} ({r.duration:.1f}s)")
    
    # 整体统计
    total_passed = sum(1 for r in results if r.status == "passed")
    total_failed = sum(1 for r in results if r.status == "failed")
    total_dur = sum(r.duration for r in results)
    terminalreporter.write_line("-" * 70)
    terminalreporter.write_line(
        f"📊 合计: {total_passed} passed, {total_failed} failed | 总耗时: {total_dur:.1f}s"
    )
    terminalreporter.write_line("=" * 70)
    
    # 输出到文件
    output_format = config.getoption("--output-format", "json")
    output_file = config.getoption("--output-file", None)
    
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
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding='utf-8')
        terminalreporter.write_line(f"\n测试结果已保存: {output_path.absolute()}")
    
    # 在 CI 环境中额外输出 JUnit XML 到默认位置
    if os.environ.get("CI") == "true" and output_format != "junit":
        junit_output = Path("reports/test-results.xml")
        junit_output.parent.mkdir(parents=True, exist_ok=True)
        junit_output.write_text(TestResultFormatter.to_junit_xml(results), encoding='utf-8')


# ========================================================================
# 页面健康度监控集成
# ========================================================================

from utils.page_health_monitor import get_page_health_monitor


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试结果钩子 - 自动记录页面健康度
    """
    outcome = yield
    report = outcome.get_result()
    
    # 只在测试调用阶段记录
    if call.when == "call":
        test_name = item.name
        # 提取模块名: tests.common.test_00_login -> common
        module_parts = item.module.__name__.split(".")
        test_module = module_parts[1] if len(module_parts) > 1 else "common"
        
        # 从测试名称推断页面名称
        page_name = _infer_page_name(test_name, test_module)
        
        # 从配置获取 URL
        url = _get_page_url(item, test_module, page_name)
        
        # 记录到健康度监控器
        monitor = get_page_health_monitor()
        monitor.record_test(
            module=test_module,
            page_name=page_name,
            url=url,
            success=report.passed
        )


def _infer_page_name(test_name: str, test_module: str) -> str:
    """从测试名称推断页面名称"""
    name = test_name.replace("test_", "")
    
    patterns = {
        "login": "login",
        "my_data": "my_data",
        "view_data": "my_data",
        "grade": "grade",
        "report": "report",
        "export": "export",
    }
    
    for pattern, page_name in patterns.items():
        if pattern in name:
            return page_name
    
    return test_module.split(".")[-1]


def _get_page_url(item, test_module: str, page_name: str) -> str:
    """获取页面 URL"""
    try:
        from config.settings import Settings
        settings = Settings()
        base_url = settings.base_url
    except:
        base_url = "http://localhost"
    
    return f"{base_url}/{test_module}/{page_name}"


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """测试会话结束钩子 - 自动生成健康度报告"""
    monitor = get_page_health_monitor()
    
    # 只有在有记录时才生成报告
    if monitor.pages:
        report = monitor.generate_health_report()
        report_path = Path("reports/page_health/health_report.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding='utf-8')
        print(f"\n📊 页面健康度报告: {report_path}")
