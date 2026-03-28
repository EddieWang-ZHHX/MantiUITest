"""
页面健康度监控器 - 基于工具自进化机制

扩展工具自进化机制，实现页面级别的监控和分析：
- 检测哪些页面需要修改（高失败率）
- 检测哪些页面应该合并（高重复度）
- 检测哪些页面应该重构（低稳定性）
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json
from collections import defaultdict
from loguru import logger
from utils.evolution.registry import ToolRegistry


@dataclass
class PageHealthRecord:
    """页面健康度记录"""
    module: str                           # 模块名称
    page_name: str                        # 页面名称
    url: str                              # 页面 URL
    
    # 健康度指标
    test_attempts: int = 0                # 测试尝试次数
    test_successes: int = 0               # 测试成功次数
    test_failures: int = 0                # 测试失败次数
    
    selector_changes: int = 0             # selector 变更次数
    exploration_failures: int = 0         # 探索失败次数
    
    last_success_time: Optional[str] = None   # 最后成功时间
    last_failure_time: Optional[str] = None   # 最后失败时间
    last_modified: Optional[str] = None       # 最后修改时间
    
    # 重复度检测
    duplicate_pages: List[str] = field(default_factory=list)  # 重复页面列表
    similar_selectors: List[str] = field(default_factory=list)  # 相似 selector 列表
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.test_attempts == 0:
            return 0.0
        return self.test_successes / self.test_attempts
    
    @property
    def health_score(self) -> float:
        """
        健康度评分 (0-100)
        
        计算公式：
        - 成功率 60%
        - 稳定性（selector 变更频率）20%
        - 探索成功率 20%
        """
        if self.test_attempts == 0:
            return 100.0  # 未测试的页面默认健康
        
        # 成功率贡献 (60%)
        success_score = self.success_rate * 60
        
        # 稳定性贡献 (20%) - selector 变更越少越好
        stability_score = max(0, 20 - self.selector_changes * 5)
        
        # 探索成功率贡献 (20%)
        if self.exploration_failures == 0:
            explore_score = 20
        else:
            explore_score = max(0, 20 - self.exploration_failures * 5)
        
        return success_score + stability_score + explore_score
    
    @property
    def needs_attention(self) -> bool:
        """是否需要关注"""
        return (
            self.health_score < 70 or
            self.success_rate < 0.5 or
            self.selector_changes >= 3 or
            self.exploration_failures >= 3
        )
    
    @property
    def should_merge(self) -> bool:
        """是否应该合并"""
        return len(self.duplicate_pages) > 0 or len(self.similar_selectors) > 5
    
    @property
    def status(self) -> str:
        """状态"""
        if self.needs_attention:
            if self.success_rate < 0.3:
                return "critical"
            else:
                return "warning"
        else:
            return "healthy"


class PageHealthMonitor:
    """
    页面健康度监控器
    
    功能：
    1. 监控页面测试成功率
    2. 检测 selector 变更频率
    3. 检测重复页面
    4. 生成优化建议
    """
    
    def __init__(self):
        self.pages: Dict[str, PageHealthRecord] = {}
        self.report_dir = Path("reports/page_health")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # 从 ToolRegistry 获取工具执行记录
        self.tool_registry = ToolRegistry()
    
    def record_test(self, module: str, page_name: str, url: str, success: bool):
        """
        记录页面测试结果
        
        Args:
            module: 模块名称
            page_name: 页面名称
            url: 页面 URL
            success: 是否成功
        """
        key = f"{module}/{page_name}"
        
        if key not in self.pages:
            self.pages[key] = PageHealthRecord(
                module=module,
                page_name=page_name,
                url=url
            )
        
        page = self.pages[key]
        page.test_attempts += 1
        
        if success:
            page.test_successes += 1
            page.last_success_time = datetime.now().isoformat()
        else:
            page.test_failures += 1
            page.last_failure_time = datetime.now().isoformat()
        
        # 持久化
        self._save_page_record(page)
        
        logger.info(f"记录页面测试: {key} - {'成功' if success else '失败'}")
    
    def record_selector_change(self, module: str, page_name: str):
        """
        记录 selector 变更
        
        Args:
            module: 模块名称
            page_name: 页面名称
        """
        key = f"{module}/{page_name}"
        
        if key not in self.pages:
            logger.warning(f"页面未注册: {key}")
            return
        
        page = self.pages[key]
        page.selector_changes += 1
        page.last_modified = datetime.now().isoformat()
        
        self._save_page_record(page)
        
        logger.info(f"记录 selector 变更: {key} - 总变更次数: {page.selector_changes}")
    
    def record_exploration_failure(self, module: str, page_name: str):
        """
        记录页面探索失败
        
        Args:
            module: 模块名称
            page_name: 页面名称
        """
        key = f"{module}/{page_name}"
        
        if key not in self.pages:
            logger.warning(f"页面未注册: {key}")
            return
        
        page = self.pages[key]
        page.exploration_failures += 1
        page.last_failure_time = datetime.now().isoformat()
        
        self._save_page_record(page)
        
        logger.warning(f"记录探索失败: {key} - 总失败次数: {page.exploration_failures}")
    
    def detect_duplicate_pages(self) -> Dict[str, List[str]]:
        """
        检测重复页面
        
        基于以下特征检测：
        1. URL 相似度
        2. selector 重叠度
        3. 测试功能重叠
        
        Returns:
            dict: {页面key: [重复页面列表]}
        """
        duplicates = {}
        
        # 简化的重复检测逻辑
        for key1, page1 in self.pages.items():
            for key2, page2 in self.pages.items():
                if key1 >= key2:
                    continue
                
                # 检测 URL 相似度
                if self._calculate_url_similarity(page1.url, page2.url) > 0.8:
                    if key1 not in duplicates:
                        duplicates[key1] = []
                    duplicates[key1].append(key2)
                    
                    # 更新记录
                    if key2 not in page1.duplicate_pages:
                        page1.duplicate_pages.append(key2)
        
        # 持久化
        for page in self.pages.values():
            if page.duplicate_pages:
                self._save_page_record(page)
        
        return duplicates
    
    def _calculate_url_similarity(self, url1: str, url2: str) -> float:
        """计算 URL 相似度"""
        # 简化实现：路径相似度
        try:
            path1 = url1.split('?')[0].rstrip('/')
            path2 = url2.split('?')[0].rstrip('/')
            
            if path1 == path2:
                return 1.0
            
            # 计算 Jaccard 相似度
            parts1 = set(path1.split('/'))
            parts2 = set(path2.split('/'))
            
            intersection = parts1 & parts2
            union = parts1 | parts2
            
            return len(intersection) / len(union) if union else 0.0
        except:
            return 0.0
    
    def generate_health_report(self) -> str:
        """
        生成健康度报告
        
        Returns:
            str: 报告 Markdown 内容
        """
        report_lines = [
            "# 页面健康度监控报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "\n## 概览\n",
            f"- 监控页面数: {len(self.pages)}",
            f"- 健康页面: {sum(1 for p in self.pages.values() if p.status == 'healthy')}",
            f"- 警告页面: {sum(1 for p in self.pages.values() if p.status == 'warning')}",
            f"- 严重页面: {sum(1 for p in self.pages.values() if p.status == 'critical')}\n",
        ]
        
        # 需要关注的页面
        attention_pages = [p for p in self.pages.values() if p.needs_attention]
        if attention_pages:
            report_lines.append("\n## 🚨 需要关注的页面\n")
            report_lines.append("| 模块 | 页面 | 健康度 | 成功率 | Selector变更 | 探索失败 | 状态 |")
            report_lines.append("|------|------|--------|--------|--------------|----------|------|")
            
            for page in sorted(attention_pages, key=lambda p: p.health_score):
                health_emoji = "🔴" if page.health_score < 50 else "🟡"
                report_lines.append(
                    f"| {page.module} | {page.page_name} | "
                    f"{health_emoji} {page.health_score:.1f} | "
                    f"{page.success_rate*100:.1f}% | "
                    f"{page.selector_changes} | "
                    f"{page.exploration_failures} | "
                    f"{page.status} |"
                )
        
        # 建议合并的页面
        merge_pages = [p for p in self.pages.values() if p.should_merge]
        if merge_pages:
            report_lines.append("\n## 🔀 建议合并的页面\n")
            report_lines.append("| 模块 | 页面 | 重复页面数量 | 重复页面列表 |")
            report_lines.append("|------|------|--------------|--------------|")
            
            for page in merge_pages:
                duplicates = ", ".join(page.duplicate_pages[:3])
                if len(page.duplicate_pages) > 3:
                    duplicates += f" ... (+{len(page.duplicate_pages)-3})"
                
                report_lines.append(
                    f"| {page.module} | {page.page_name} | "
                    f"{len(page.duplicate_pages)} | "
                    f"{duplicates} |"
                )
        
        # 所有页面详情
        report_lines.append("\n## 📋 所有页面详情\n")
        report_lines.append("| 模块 | 页面 | 健康度 | 测试次数 | 成功率 | Selector变更 | 最后成功 |")
        report_lines.append("|------|------|--------|----------|--------|--------------|----------|")
        
        for page in sorted(self.pages.values(), key=lambda p: p.health_score, reverse=True):
            health_emoji = "🟢" if page.status == "healthy" else ("🟡" if page.status == "warning" else "🔴")
            last_success = page.last_success_time[:10] if page.last_success_time else "N/A"
            
            report_lines.append(
                f"| {page.module} | {page.page_name} | "
                f"{health_emoji} {page.health_score:.1f} | "
                f"{page.test_attempts} | "
                f"{page.success_rate*100:.1f}% | "
                f"{page.selector_changes} | "
                f"{last_success} |"
            )
        
        # 优化建议
        report_lines.append("\n## 💡 优化建议\n")
        
        suggestions = []
        
        # 健康度低的页面
        critical_pages = [p for p in self.pages.values() if p.health_score < 50]
        if critical_pages:
            suggestions.append("### 紧急修复")
            suggestions.append("以下页面健康度低于50，需要优先修复：\n")
            for page in critical_pages:
                suggestions.append(f"- **{page.module}/{page.page_name}** (健康度: {page.health_score:.1f})")
                if page.success_rate < 0.3:
                    suggestions.append(f"  - 建议：检查页面是否已下线或大幅改版")
                if page.selector_changes >= 3:
                    suggestions.append(f"  - 建议：使用更稳定的 selector 策略（如 data-* 属性）")
                if page.exploration_failures >= 3:
                    suggestions.append(f"  - 建议：手动探索页面，更新 POM 代码")
        
        # 建议合并的页面
        merge_pages = [p for p in self.pages.values() if p.should_merge]
        if merge_pages:
            suggestions.append("\n### 页面合并")
            suggestions.append("以下页面存在重复，建议合并：\n")
            for page in merge_pages:
                suggestions.append(f"- **{page.module}/{page.page_name}**")
                suggestions.append(f"  - 重复页面: {', '.join(page.duplicate_pages[:3])}")
                suggestions.append(f"  - 建议：合并为统一的 POM 类，使用参数化区分")
        
        # 长期未成功
        old_failures = [
            p for p in self.pages.values()
            if p.test_failures > 0 and p.last_success_time and
            (datetime.now() - datetime.fromisoformat(p.last_success_time)).days > 7
        ]
        if old_failures:
            suggestions.append("\n### 长期失败")
            suggestions.append("以下页面超过7天未成功，可能已下线：\n")
            for page in old_failures:
                suggestions.append(f"- **{page.module}/{page.page_name}**")
                suggestions.append(f"  - 最后成功: {page.last_success_time[:10]}")
                suggestions.append(f"  - 建议：确认页面是否仍需测试")
        
        if suggestions:
            report_lines.extend(suggestions)
        else:
            report_lines.append("\n所有页面运行正常，暂无优化建议。✅")
        
        report_content = "\n".join(report_lines)
        
        # 保存报告
        report_file = self.report_dir / "health_report.md"
        report_file.write_text(report_content, encoding='utf-8')
        logger.info(f"健康度报告已生成: {report_file}")
        
        return report_content
    
    def _save_page_record(self, page: PageHealthRecord):
        """保存页面记录"""
        record_file = self.report_dir / f"{page.module}_{page.page_name}.json"
        
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump({
                'module': page.module,
                'page_name': page.page_name,
                'url': page.url,
                'test_attempts': page.test_attempts,
                'test_successes': page.test_successes,
                'test_failures': page.test_failures,
                'selector_changes': page.selector_changes,
                'exploration_failures': page.exploration_failures,
                'last_success_time': page.last_success_time,
                'last_failure_time': page.last_failure_time,
                'last_modified': page.last_modified,
                'duplicate_pages': page.duplicate_pages,
                'similar_selectors': page.similar_selectors
            }, f, ensure_ascii=False, indent=2)
    
    def load_all_records(self):
        """加载所有页面记录"""
        if not self.report_dir.exists():
            return
        
        for record_file in self.report_dir.glob("*.json"):
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                key = f"{data['module']}/{data['page_name']}"
                self.pages[key] = PageHealthRecord(
                    module=data['module'],
                    page_name=data['page_name'],
                    url=data['url'],
                    test_attempts=data.get('test_attempts', 0),
                    test_successes=data.get('test_successes', 0),
                    test_failures=data.get('test_failures', 0),
                    selector_changes=data.get('selector_changes', 0),
                    exploration_failures=data.get('exploration_failures', 0),
                    last_success_time=data.get('last_success_time'),
                    last_failure_time=data.get('last_failure_time'),
                    last_modified=data.get('last_modified'),
                    duplicate_pages=data.get('duplicate_pages', []),
                    similar_selectors=data.get('similar_selectors', [])
                )
            except Exception as e:
                logger.error(f"加载页面记录失败: {record_file} - {e}")
    
    def integrate_with_evolution(self):
        """
        与工具自进化机制集成
        
        从 ToolRegistry 读取工具执行记录，推断页面健康度
        """
        # 读取 page_explorer 工具记录
        for tool_name, record in self.tool_registry.tools.items():
            if not tool_name.startswith('page_explorer.'):
                continue
            
            # 解析工具名：page_explorer.explore -> explore
            parts = tool_name.split('.')
            if len(parts) < 2:
                continue
            
            action = parts[1]
            
            if action == 'explore':
                # 探索失败的页面
                if record.failures > 0:
                    # 从失败上下文中提取页面信息
                    for ctx in record.failure_contexts:
                        args = ctx.get('args', '()')
                        # 简化解析（实际需要更健壮的解析）
                        if 'module=' in str(args) and 'page_name=' in str(args):
                            # 这里需要实际解析参数
                            pass


# 全局单例
_monitor_instance = None

def get_page_health_monitor() -> PageHealthMonitor:
    """获取页面健康度监控器单例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PageHealthMonitor()
        _monitor_instance.load_all_records()
    return _monitor_instance
