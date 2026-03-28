"""
工具注册表 - 管理所有工具的执行历史和进化状态

借鉴 Yunjue-Agent 的工具管理机制，实现工具的自动进化。
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import json
from loguru import logger


@dataclass
class ToolRecord:
    """工具记录"""
    name: str                           # 工具名称
    module: str                         # 所属模块
    file_path: str                      # 文件路径
    status: str = "untested"            # untested, verified, failed, quarantined
    attempts: int = 0                   # 总执行次数
    successes: int = 0                  # 成功次数
    failures: int = 0                   # 连续失败次数
    failure_contexts: List[Dict] = field(default_factory=list)  # 失败上下文
    llm_analysis: Optional[str] = None  # LLM 分析结果
    evolution_history: List[Dict] = field(default_factory=list)  # 进化历史


class ToolRegistry:
    """
    工具注册表 - 单例模式
    
    职责：
    1. 注册和管理所有工具
    2. 记录工具执行历史
    3. 检测连续失败并触发进化
    4. 持久化工具记录和进化报告
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.tools: Dict[str, ToolRecord] = {}
        self.config = self._load_config()
        self.llm_client = None
        
        # 确保报告目录存在
        self.report_dir = Path(self.config.get('report_dir', 'reports/evolution'))
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> dict:
        """加载配置"""
        try:
            from config.settings import Settings
            settings = Settings()
            return settings.evolution
        except Exception as e:
            logger.warning(f"加载进化配置失败: {e}，使用默认配置")
            return {
                'enabled': False,
                'failure_threshold': 3,
                'monitor_dirs': ['scripts', 'utils'],
                'report_dir': 'reports/evolution',
                'auto_apply': False
            }
    
    def register(self, name: str, module: str, file_path: str):
        """
        注册工具
        
        Args:
            name: 工具名称
            module: 所属模块
            file_path: 文件路径
        """
        if name not in self.tools:
            self.tools[name] = ToolRecord(
                name=name,
                module=module,
                file_path=file_path
            )
            logger.debug(f"注册工具: {name} ({module})")
    
    def record_execution(self, name: str, success: bool, context: Dict):
        """
        记录工具执行结果
        
        Args:
            name: 工具名称
            success: 是否成功
            context: 执行上下文（参数、错误等）
        """
        if name not in self.tools:
            logger.warning(f"工具未注册: {name}")
            return
        
        tool = self.tools[name]
        tool.attempts += 1
        
        if success:
            tool.successes += 1
            tool.failures = 0  # 重置连续失败计数
            
            if tool.status in ["untested", "failed"]:
                tool.status = "verified"
                logger.info(f"工具验证成功: {name}")
        else:
            tool.failures += 1
            tool.failure_contexts.append({
                **context,
                'timestamp': datetime.now().isoformat()
            })
            
            # 持久化失败记录
            self._save_record(tool)
            
            # 检查是否达到失败阈值
            threshold = self.config.get('failure_threshold', 3)
            if tool.failures >= threshold:
                tool.status = "quarantined"
                logger.warning(f"工具进入隔离状态: {name} (连续失败 {tool.failures} 次)")
                
                # 触发进化
                if self.config.get('enabled', False):
                    self._trigger_evolution(name)
    
    def _trigger_evolution(self, name: str):
        """
        触发工具进化
        
        Args:
            name: 工具名称
        """
        from utils.evolution.enhancer import ToolEnhancer
        
        tool = self.tools[name]
        logger.info(f"开始工具进化: {name}")
        
        try:
            enhancer = ToolEnhancer(self._get_llm_client())
            
            # 1. 用 LLM 分析失败原因
            analysis = enhancer.analyze_failure(tool)
            tool.llm_analysis = json.dumps(analysis, ensure_ascii=False)
            
            logger.info(f"失败分析完成: {analysis.get('type', 'Unknown')}")
            
            # 2. 如果是 Execution Failure，生成新工具代码
            if analysis.get('type') == 'execution_failure':
                new_code = enhancer.generate_tool_code(tool, analysis)
                
                # 3. 验证新工具
                if enhancer.validate_tool(new_code):
                    # 4. 根据配置决定是否自动应用
                    auto_apply = self.config.get('auto_apply', False)
                    
                    if auto_apply:
                        self._reload_tool(name, new_code)
                        logger.info(f"工具自动进化成功: {name}")
                    else:
                        # 保存建议代码到文件
                        self._save_evolution_suggestion(tool, new_code, analysis)
                        logger.info(f"工具进化建议已保存，请人工审核: {name}")
                    
                    # 5. 记录进化历史
                    tool.evolution_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'analysis': analysis,
                        'auto_applied': auto_apply
                    })
                    
                    # 6. 重置状态
                    tool.failures = 0
                    tool.status = "untested" if auto_apply else "quarantined"
            
            # 持久化
            self._save_record(tool)
            self._save_evolution_report(tool)
            
        except Exception as e:
            logger.error(f"工具进化失败: {name}, 错误: {e}")
    
    def _get_llm_client(self):
        """获取 LLM 客户端"""
        if self.llm_client is None:
            from utils.evolution.llm_client import LLMClient
            from config.settings import Settings
            
            settings = Settings()
            self.llm_client = LLMClient(settings.llm)
        
        return self.llm_client
    
    def _save_record(self, tool: ToolRecord):
        """保存工具记录到 JSON"""
        record_file = self.report_dir / f"{tool.name.replace('.', '_')}.json"
        
        try:
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(tool), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存工具记录失败: {e}")
    
    def _save_evolution_suggestion(self, tool: ToolRecord, new_code: str, analysis: Dict):
        """保存进化建议到文件"""
        suggestion_file = self.report_dir / f"{tool.name.replace('.', '_')}_suggested.py"
        
        try:
            with open(suggestion_file, 'w', encoding='utf-8') as f:
                f.write(f"# 工具进化建议\n")
                f.write(f"# 原始文件: {tool.file_path}\n")
                f.write(f"# 分析时间: {datetime.now().isoformat()}\n")
                f.write(f"# 失败原因: {analysis.get('reason', 'Unknown')}\n")
                f.write(f"# 改进建议: {analysis.get('suggestion', 'Unknown')}\n\n")
                f.write(new_code)
            
            logger.info(f"进化建议已保存: {suggestion_file}")
        except Exception as e:
            logger.error(f"保存进化建议失败: {e}")
    
    def _save_evolution_report(self, tool: ToolRecord):
        """保存进化报告到 Markdown"""
        report_file = self.report_dir / f"{tool.name.replace('.', '_')}_report.md"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"# 工具进化报告: {tool.name}\n\n")
                f.write(f"## 基本信息\n\n")
                f.write(f"- **模块**: {tool.module}\n")
                f.write(f"- **文件**: {tool.file_path}\n")
                f.write(f"- **状态**: {tool.status}\n")
                f.write(f"- **执行次数**: {tool.attempts}\n")
                f.write(f"- **成功次数**: {tool.successes}\n")
                f.write(f"- **连续失败**: {tool.failures}\n\n")
                
                if tool.failure_contexts:
                    f.write(f"## 最近失败上下文\n\n")
                    for ctx in tool.failure_contexts[-3:]:
                        f.write(f"### {ctx.get('timestamp', 'Unknown')}\n\n")
                        f.write(f"```json\n{json.dumps(ctx, ensure_ascii=False, indent=2)}\n```\n\n")
                
                if tool.llm_analysis:
                    f.write(f"## LLM 分析\n\n")
                    f.write(f"```json\n{tool.llm_analysis}\n```\n\n")
                
                if tool.evolution_history:
                    f.write(f"## 进化历史\n\n")
                    for hist in tool.evolution_history:
                        f.write(f"- {hist.get('timestamp')}: {hist.get('analysis', {}).get('type', 'Unknown')}\n")
            
            logger.info(f"进化报告已保存: {report_file}")
        except Exception as e:
            logger.error(f"保存进化报告失败: {e}")
    
    def _reload_tool(self, name: str, new_code: str):
        """
        重新加载工具（谨慎使用）
        
        Args:
            name: 工具名称
            new_code: 新的工具代码
        """
        tool = self.tools[name]
        
        try:
            # 1. 备份原始文件
            backup_file = Path(tool.file_path).with_suffix('.py.bak')
            Path(tool.file_path).rename(backup_file)
            
            # 2. 写入新代码
            with open(tool.file_path, 'w', encoding='utf-8') as f:
                f.write(new_code)
            
            # 3. 重新加载模块
            import importlib
            import sys
            
            module_name = tool.module
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            
            logger.info(f"工具重新加载成功: {name}")
            
        except Exception as e:
            logger.error(f"重新加载工具失败: {e}")
            
            # 恢复备份
            if backup_file.exists():
                backup_file.rename(tool.file_path)
                logger.info(f"已恢复原始文件: {tool.file_path}")
    
    def get_tool_summary(self) -> Dict:
        """获取工具摘要统计"""
        total = len(self.tools)
        verified = sum(1 for t in self.tools.values() if t.status == "verified")
        quarantined = sum(1 for t in self.tools.values() if t.status == "quarantined")
        
        return {
            'total': total,
            'verified': verified,
            'quarantined': quarantined,
            'success_rate': verified / total if total > 0 else 0
        }