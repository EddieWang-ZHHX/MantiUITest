"""证据管理器 - 管理测试证据文件

功能：
1. 固定命名：screenshot.png, video.webm, trace.zip, page.html
2. History：每次运行前备份上次的证据到 history/
3. 查找：提供方法查找最新证据
"""
from pathlib import Path
from datetime import datetime
import shutil
from typing import Dict, Optional


class EvidenceManager:
    """证据管理器"""
    
    EVIDENCE_DIR = Path("reports/evidence")
    HISTORY_DIR = EVIDENCE_DIR / "history"
    
    # 固定文件名
    SCREENSHOT = "screenshot.png"
    VIDEO = "video.webm"
    TRACE = "trace.zip"
    PAGE_HTML = "page.html"
    
    @classmethod
    def prepare_for_test(cls, test_name: str) -> Path:
        """准备测试证据目录
        
        Args:
            test_name: 测试名称
            
        Returns:
            Path: 证据目录路径
        """
        # 创建证据目录
        evidence_dir = cls.EVIDENCE_DIR / test_name
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份上次的证据到 history
        if evidence_dir.exists():
            # 检查是否有文件
            existing_files = list(evidence_dir.glob("*"))
            if existing_files:
                # 移动到 history
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                history_dir = cls.HISTORY_DIR / f"{timestamp}_{test_name}"
                history_dir.mkdir(parents=True, exist_ok=True)
                
                for f in existing_files:
                    if f.name not in [cls.SCREENSHOT, cls.VIDEO, cls.TRACE, cls.PAGE_HTML]:
                        # 只备份非固定命名的文件（如旧的截图等）
                        try:
                            shutil.move(str(f), str(history_dir / f.name))
                        except:
                            pass
                
                # 也备份固定文件（如果有）
                for fixed_file in [cls.SCREENSHOT, cls.VIDEO, cls.TRACE, cls.PAGE_HTML]:
                    src = evidence_dir / fixed_file
                    if src.exists():
                        try:
                            shutil.move(str(src), str(history_dir / fixed_file))
                        except:
                            pass
        
        return evidence_dir
    
    @classmethod
    def get_evidence_path(cls, test_name: str, file_type: str) -> Path:
        """获取证据文件路径
        
        Args:
            test_name: 测试名称
            file_type: 文件类型 (screenshot, video, trace, page)
            
        Returns:
            Path: 证据文件路径
        """
        evidence_dir = cls.EVIDENCE_DIR / test_name
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        file_map = {
            "screenshot": cls.SCREENSHOT,
            "video": cls.VIDEO,
            "trace": cls.TRACE,
            "page": cls.PAGE_HTML,
        }
        
        filename = file_map.get(file_type, file_type)
        return evidence_dir / filename
    
    @classmethod
    def save_evidence(cls, test_name: str, page, trace_context=None) -> Dict[str, Path]:
        """保存证据文件（固定命名）
        
        Args:
            test_name: 测试名称
            page: Playwright Page 对象
            trace_context: Playwright tracing stop result
            
        Returns:
            Dict: 证据文件路径
        """
        evidence_dir = cls.prepare_for_test(test_name)
        
        result = {}
        
        # 保存截图
        try:
            screenshot_path = evidence_dir / cls.SCREENSHOT
            page.screenshot(path=str(screenshot_path), full_page=True)
            result["screenshot"] = screenshot_path
        except Exception as e:
            result["screenshot"] = None
        
        # 保存页面 HTML
        try:
            html_path = evidence_dir / cls.PAGE_HTML
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page.content())
            result["page"] = html_path
        except Exception as e:
            result["page"] = None
        
        # 停止 trace
        if trace_context:
            try:
                trace_path = evidence_dir / cls.TRACE
                trace_context.stop(path=str(trace_path))
                result["trace"] = trace_path
            except Exception as e:
                result["trace"] = None
        
        # 视频在 context.close() 时会自动保存到 evidence_dir
        # 查找视频文件
        video_files = list(evidence_dir.glob("*.webm"))
        if video_files:
            # 重命名为固定名称
            video_path = evidence_dir / cls.VIDEO
            # 删除旧的
            if video_path.exists():
                video_path.unlink()
            # 重命名新的
            latest_video = max(video_files, key=lambda p: p.stat().st_mtime)
            shutil.move(str(latest_video), str(video_path))
            result["video"] = video_path
        else:
            result["video"] = None
        
        return result
    
    @classmethod
    def get_latest_evidence(cls, test_name: str) -> Dict[str, Optional[Path]]:
        """获取最新证据文件路径
        
        Args:
            test_name: 测试名称
            
        Returns:
            Dict: 证据文件路径字典
        """
        evidence_dir = cls.EVIDENCE_DIR / test_name
        
        return {
            "screenshot": evidence_dir / cls.SCREENSHOT if (evidence_dir / cls.SCREENSHOT).exists() else None,
            "video": evidence_dir / cls.VIDEO if (evidence_dir / cls.VIDEO).exists() else None,
            "trace": evidence_dir / cls.TRACE if (evidence_dir / cls.TRACE).exists() else None,
            "page": evidence_dir / cls.PAGE_HTML if (evidence_dir / cls.PAGE_HTML).exists() else None,
        }
    
    @classmethod
    def format_evidence_links(cls, test_name: str) -> str:
        """格式化证据链接（用于报告）
        
        Args:
            test_name: 测试名称
            
        Returns:
            str: Markdown 格式的证据链接
        """
        evidence = cls.get_latest_evidence(test_name)
        links = []
        
        for key, path in evidence.items():
            if path and path.exists():
                abs_path = path.absolute()
                file_url = f"file:///{str(abs_path).replace(chr(92), '/')}"
                icon = {
                    "screenshot": "📷",
                    "video": "🎬",
                    "trace": "🔍",
                    "page": "📄"
                }.get(key, "📎")
                links.append(f'{icon} [{key.upper()}]({file_url})')
        
        return " | ".join(links) if links else "无证据"
