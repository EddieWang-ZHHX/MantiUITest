"""工具模块

公共接口：
- logger: 日志
- BrowserManager: 浏览器管理器（框架内部使用）

内部模块 (_core/): 框架内部使用，测试不应直接导入
- browser_manager
- evidence_manager
- page_analyzer
- test_formatter

脚本 (_scripts/): 独立脚本，直接运行
- check_naming_rules.py
- evidence_cleaner.py
- report_generator.py
"""

from .logger import logger

__all__ = ["logger"]
