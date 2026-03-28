"""
工具自进化框架

借鉴 Yunjue-Agent 的 enhance_tools() 机制，实现工具类的自动进化能力。

核心组件：
- ToolRegistry: 工具注册表，管理所有工具的执行历史和进化状态
- LLMClient: LLM 客户端，支持任何兼容 OpenAI API 的本地模型
- ToolEnhancer: 工具进化增强器，分析失败原因并生成改进代码
- evolution_monitor: 装饰器，监控工具执行并触发进化
- ToolScanner: 目录扫描器，自动扫描 scripts/ 和 utils/ 目录
"""

from utils.evolution.registry import ToolRegistry, ToolRecord
from utils.evolution.llm_client import LLMClient
from utils.evolution.enhancer import ToolEnhancer
from utils.evolution.decorator import evolution_monitor
from utils.evolution.scanner import ToolScanner

__all__ = [
    'ToolRegistry',
    'ToolRecord',
    'LLMClient',
    'ToolEnhancer',
    'evolution_monitor',
    'ToolScanner',
]