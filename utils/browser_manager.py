"""浏览器管理工具 - 支持视频录制和证据收集

证据文件命名规范：
- screenshot.png: 截图
- video.webm: 视频录制
- trace.zip: Playwright Trace
- page.html: 页面 HTML
"""
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional, Dict
from pathlib import Path
from config.settings import Settings
from utils.logger import logger
import shutil


class BrowserManager:
    """浏览器管理器 - 支持完整的证据收集"""
    
    # 固定证据文件名
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
        self.video_path: Optional[str] = None
        self.trace_path: Optional[str] = None
        self.test_name: str = "unknown"
        self.evidence_dir: Optional[Path] = None
        self._trace_started = False
    
    def start_browser(self, test_name: str = "test", module: str = ""):
        """启动浏览器
        
        Args:
            test_name: 测试名称（用于证据目录）
            module: 模块名称（可选，用于 reports/evidence/{module}/{test_name}/ 结构）
        """
        self.test_name = test_name
        self.playwright = sync_playwright().start()
        
        browser_config = self.settings.browser
        evidence_config = self.settings.get('evidence', {})
        
        # 根据配置选择浏览器引擎
        browser_name = browser_config.get('name', 'chromium')
        launcher = getattr(self.playwright, browser_name)
        
        # 准备证据收集目录：reports/evidence/{module}/{test_name}/
        if module:
            self.evidence_dir = Path("reports/evidence") / module / self.test_name
        else:
            self.evidence_dir = Path("reports/evidence") / self.test_name
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置视频录制
        video_settings = {}
        if evidence_config.get('video', 'on_failure') != 'never':
            video_settings = {
                "record_video_dir": str(self.evidence_dir),
                "record_video_size": {"width": 1920, "height": 1080}
            }
            logger.debug(f"视频录制已启用")
        
        # 启动浏览器
        self.browser = launcher.launch(
            headless=browser_config.get('headless', True),
            slow_mo=browser_config.get('slow_mo', 0),
            args=browser_config.get('args', [])
        )
        
        # 创建上下文（带视频录制）
        viewport = browser_config.get('viewport', {'width': 1920, 'height': 1080})
        self.context = self.browser.new_context(
            viewport=viewport,
            ignore_https_errors=True,
            **video_settings
        )
        
        # 开始录制 Trace（如果启用）- 只在需要时录制
        trace_mode = evidence_config.get('trace', 'on_failure')
        if trace_mode and trace_mode != 'never':
            # 总是开始录制，但只在失败时保存
            self.trace_path = str(self.evidence_dir / self.TRACE)
            self.context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True
            )
            self._trace_started = True
            logger.debug(f"Trace 录制已启用")
        
        # 创建页面
        self.page = self.context.new_page()
        
        # 设置默认超时
        timeout = self.settings.test.get('timeout', 30000)
        self.page.set_default_timeout(timeout)
        
        # 监听控制台消息
        if evidence_config.get('console_log', True):
            self.page.on("console", lambda msg: logger.debug(f"浏览器控制台 [{msg.type}]: {msg.text}"))
        
        # 监听页面错误
        self.page.on("pageerror", lambda err: logger.error(f"页面错误：{err}"))
        
        logger.info(f"浏览器已启动，测试：{self.test_name}")
        return self.page
    
    def save_evidence(self, test_status: str = "failed") -> Dict[str, Optional[str]]:
        """保存测试证据
        
        Args:
            test_status: 测试状态 "passed" 或 "failed"
            
        Returns:
            Dict: 证据文件路径字典
        """
        evidence_config = self.settings.get('evidence', {})
        result = {
            "screenshot": None,
            "video": None,
            "trace": None,
            "page": None
        }
        
        if not self.evidence_dir:
            return result
        
        logger.info(f"保存测试证据，状态：{test_status}")
        
        # 是否需要收集证据
        is_failure = test_status == "failed"
        should_save = lambda key: (
            evidence_config.get(key, 'on_failure') == 'always' or
            (is_failure and evidence_config.get(key, 'on_failure') == 'on_failure')
        )
        
        # 保存截图
        if should_save('screenshot'):
            try:
                screenshot_path = self.evidence_dir / self.SCREENSHOT
                self.page.screenshot(path=str(screenshot_path), full_page=True)
                result["screenshot"] = str(screenshot_path)
                logger.info(f"截图已保存：{screenshot_path}")
            except Exception as e:
                logger.error(f"保存截图失败：{e}")
        
        # 保存页面 HTML
        if should_save('page_html'):
            try:
                html_path = self.evidence_dir / self.PAGE_HTML
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(self.page.content())
                result["page"] = str(html_path)
                logger.info(f"页面 HTML 已保存：{html_path}")
            except Exception as e:
                logger.error(f"保存 HTML 失败：{e}")
        
        # 保存 Trace（失败时）
        if should_save('trace') and self._trace_started and self.trace_path:
            try:
                self.context.tracing.stop(path=self.trace_path)
                result["trace"] = self.trace_path
                logger.info(f"Trace 已保存：{self.trace_path}")
            except Exception as e:
                logger.error(f"保存 Trace 失败：{e}")
        
        return result
    
    def close(self):
        """关闭浏览器"""
        try:
            if self.context:
                # 先停止 Trace（如果还在录制）
                if self._trace_started:
                    try:
                        self.context.tracing.stop()
                    except:
                        pass
                
                self.context.close()
                
                # 处理视频文件
                if self.evidence_dir:
                    video_files = list(self.evidence_dir.glob("*.webm"))
                    if video_files:
                        # 重命名最新视频为固定名称
                        latest_video = max(video_files, key=lambda p: p.stat().st_mtime)
                        target_video = self.evidence_dir / self.VIDEO
                        
                        # 删除旧的
                        if target_video.exists():
                            target_video.unlink()
                        
                        # 重命名新的
                        shutil.move(str(latest_video), str(target_video))
                        logger.info(f"视频已保存：{target_video}")
        except Exception as e:
            logger.error(f"关闭浏览器时出错：{e}")
        
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"关闭浏览器时出错：{e}")
    
    def get_page(self) -> Optional[Page]:
        """获取当前页面"""
        return self.page
