"""浏览器管理工具 - 支持完整证据收集 (video/trace/screenshot/html)

关键设计：
1. session 级 Playwright 实例（整个 pytest session 只启动一次）
2. function 级 context + page（每个测试独立，可保存完整证据）
3. 视频路径用 page.video.path() 精确获取，避免 glob 冲突
4. 证据保存顺序：screenshot → page_html → trace → video → close page → close context
"""
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional, Dict
from pathlib import Path
from config.settings import Settings
from utils.logger import logger
import shutil


class BrowserManager:
    """浏览器管理器"""

    SCREENSHOT = "screenshot.png"
    VIDEO = "video.webm"
    TRACE = "trace.zip"
    PAGE_HTML = "page.html"

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.trace_path: Optional[str] = None
        self.test_name: str = "unknown"
        self.evidence_dir: Optional[Path] = None
        self._trace_started = False
        self._browser_launched = False
        self._session_page_created = False
        self._current_video_path: Optional[str] = None

    def start_browser(self, test_name: str = "uitest"):
        """启动/复用浏览器（session 级，整个 session 只执行一次）"""
        self.test_name = test_name
        if self._browser_launched:
            logger.debug(f"浏览器已存在，复用，测试：{self.test_name}")
            return
        self.playwright = sync_playwright().start()
        browser_config = self.settings.browser
        browser_name = browser_config.get('name', 'chromium')
        launcher = getattr(self.playwright, browser_name)
        self.browser = launcher.launch(
            headless=browser_config.get('headless', True),
            slow_mo=browser_config.get('slow_mo', 0),
            args=browser_config.get('args', [])
        )
        self._browser_launched = True
        logger.info(f"浏览器已启动（session 级）")

    def _rebuild_context(self):
        """重建 context + page（每个测试开始时调用，获得独立视频和 trace）"""
        if self.context:
            try:
                if self._trace_started:
                    try:
                        self.context.tracing.stop()
                    except Exception:
                        pass
                    self._trace_started = False
                self.context.close()
            except Exception:
                pass
            self.context = None
            self.page = None

        self.evidence_dir = Path("reports/evidence")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        evidence_config = self.settings.get('evidence', {})
        viewport = self.settings.browser.get('viewport', {'width': 1920, 'height': 1080})
        video_settings = {
            "record_video_dir": str(self.evidence_dir),
            "record_video_size": {"width": 1920, "height": 1080}
        }
        self.context = self.browser.new_context(
            viewport=viewport,
            ignore_https_errors=True,
            **video_settings
        )
        self.page = self.context.new_page()
        timeout = self.settings.test.get('timeout', 30000)
        self.page.set_default_timeout(timeout)
        if evidence_config.get('console_log', True):
            self.page.on("console", lambda msg: logger.debug(f" [{msg.type}] {msg.text}"))
        self.page.on("pageerror", lambda err: logger.error(f"页面错误：{err}"))

        # 启动 Trace
        trace_mode = evidence_config.get('trace', 'on_failure')
        if trace_mode and trace_mode != 'never':
            self.trace_path = str(self.evidence_dir / self.TRACE)
            self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
            self._trace_started = True
            logger.debug(f"Trace 录制已启用")

        # 记录视频路径（page.video 在 context close 前都有效）
        self._current_video_path = None
        if hasattr(self.page, 'video') and self.page.video:
            try:
                self._current_video_path = self.page.video.path()
            except Exception:
                pass

        self._session_page_created = True
        logger.info("Context + Page 已重建（独立视频+Trace）")

    def save_evidence(self, test_status: str = "passed", test_name: str = "") -> Dict[str, Optional[str]]:
        """保存测试证据

        正确顺序（避免 WinError 32）：
        1. screenshot  — page 仍 open
        2. page_html  — page 仍 open
        3. trace      — context 仍 open
        4. video      — page.video.save_as() 需要 page 未关闭
        5. close page — save_as 之后
        6. close context
        """
        evidence_config = self.settings.get('evidence', {})
        result = {"screenshot": None, "video": None, "trace": None, "page": None}

        if test_name:
            evidence_dir = self.evidence_dir / test_name
        else:
            evidence_dir = self.evidence_dir

        if not evidence_dir:
            return result

        evidence_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"保存证据 [{test_name}]，状态：{test_status}")

        is_failure = test_status == "failed"

        def should_save(key):
            mode = evidence_config.get(key, 'on_failure')
            return mode == 'always' or (is_failure and mode == 'on_failure')

        # 1. 截图
        if should_save('screenshot') and self.page:
            try:
                sp = evidence_dir / self.SCREENSHOT
                self.page.screenshot(path=str(sp), full_page=True)
                result["screenshot"] = str(sp)
                logger.info(f"截图已保存：{sp}")
            except Exception as e:
                logger.error(f"保存截图失败：{e}")

        # 2. HTML（page close 之前）
        if should_save('page_html') and self.page:
            try:
                hp = evidence_dir / self.PAGE_HTML
                with open(hp, 'w', encoding='utf-8') as f:
                    f.write(self.page.content())
                result["page"] = str(hp)
                logger.info(f"HTML 已保存：{hp}")
            except Exception as e:
                logger.error(f"保存 HTML 失败：{e}")

        # 3. Trace（context close 之前）
        if should_save('trace') and self._trace_started and self.trace_path and self.context:
            try:
                tp = evidence_dir / "trace.zip"
                self.context.tracing.stop(path=str(tp))
                result["trace"] = str(tp)
                logger.info(f"Trace 已保存：{tp}")
            except Exception as e:
                logger.error(f"保存 Trace 失败：{e}")

        # 4. 视频（先获取路径，关闭 page，再 copy 避免截断）
        if should_save('video') and self.page and hasattr(self.page, 'video') and self.page.video:
            try:
                vp = evidence_dir / self.VIDEO
                # 先获取当前视频路径（page close 前有效）
                video_src_path = self.page.video.path()
                # 关闭 page 后视频文件才完整
                self.page.close()
                self.page = None
                import shutil
                # 等待文件写完（Windows 需要）
                import time
                time.sleep(0.5)
                if video_src_path and Path(video_src_path).exists():
                    shutil.copy2(video_src_path, str(vp))
                    if vp.exists():
                        result["video"] = str(vp)
                        logger.info(f"视频已保存：{vp} ({vp.stat().st_size / 1024:.1f} KB)")
                else:
                    logger.error(f"保存视频失败：视频文件不存在 {video_src_path}")
            except Exception as e:
                logger.error(f"保存视频失败：{e}")

        # 5. 关闭 page
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass
            self.page = None

        # 6. 关闭 context
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None

        # 重置状态，让下一个测试重新启动浏览器
        self._browser_launched = False
        return result

    def close(self):
        """关闭浏览器（session 结束时调用）"""
        if self.context:
            try:
                if self._trace_started:
                    try:
                        self.context.tracing.stop()
                    except Exception:
                        pass
                    self._trace_started = False
                self.context.close()
            except Exception:
                pass
            self.context = None
            self.page = None
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
        self._browser_launched = False
        logger.info("浏览器已关闭")

    def get_page(self) -> Optional[Page]:
        """获取当前页面"""
        return self.page
