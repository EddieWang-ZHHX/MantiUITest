"""
工具扫描器 - 自动扫描 scripts/ 和 utils/ 目录

扫描指定目录下的所有 Python 文件，注册工具函数到 ToolRegistry。
"""

import os
import inspect
from pathlib import Path
from loguru import logger


class ToolScanner:
    """
    工具扫描器
    
    职责：
    1. 扫描指定目录下的 Python 文件
    2. 发现所有工具函数
    3. 注册到 ToolRegistry
    """
    
    def __init__(self):
        """初始化工具扫描器"""
        from utils.evolution.registry import ToolRegistry
        self.registry = ToolRegistry()
    
    def scan_all(self):
        """扫描所有目标目录"""
        from config.settings import Settings
        
        settings = Settings()
        monitor_dirs = settings.get('evolution.monitor_dirs', ['scripts', 'utils'])
        
        logger.info(f"开始扫描目录: {monitor_dirs}")
        
        total_tools = 0
        for dir_name in monitor_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                count = self._scan_directory(dir_path)
                total_tools += count
                logger.info(f"扫描 {dir_name}: 发现 {count} 个工具函数")
            else:
                logger.warning(f"目录不存在: {dir_name}")
        
        logger.info(f"扫描完成: 共发现 {total_tools} 个工具函数")
    
    def _scan_directory(self, dir_path: Path) -> int:
        """
        扫描单个目录
        
        Args:
            dir_path: 目录路径
        
        Returns:
            发现的工具函数数量
        """
        count = 0
        
        for py_file in dir_path.rglob('*.py'):
            # 跳过特定文件
            if self._should_skip_file(py_file):
                continue
            
            # 转换为模块名
            module_name = self._file_to_module(py_file)
            
            try:
                # 导入模块
                import importlib
                module = importlib.import_module(module_name)
                
                # 查找所有可调用的函数
                for name, obj in inspect.getmembers(module):
                    if self._is_tool_function(name, obj):
                        # 注册工具
                        tool_name = f"{module_name}.{name}"
                        self.registry.register(
                            name=tool_name,
                            module=module_name,
                            file_path=str(py_file)
                        )
                        count += 1
                        
            except Exception as e:
                logger.warning(f"扫描失败: {py_file}, 错误: {e}")
        
        return count
    
    def _should_skip_file(self, py_file: Path) -> bool:
        """
        判断是否应该跳过文件
        
        Args:
            py_file: Python 文件路径
        
        Returns:
            是否跳过
        """
        # 跳过 __pycache__
        if '__pycache__' in str(py_file):
            return True
        
        # 跳过测试文件
        if py_file.name.startswith('test_'):
            return True
        
        # 跳过 __init__.py
        if py_file.name == '__init__.py':
            return True
        
        # 跳过 evolution 目录本身
        if 'evolution' in str(py_file):
            return True
        
        return False
    
    def _is_tool_function(self, name: str, obj) -> bool:
        """
        判断是否是工具函数
        
        Args:
            name: 函数名
            obj: 函数对象
        
        Returns:
            是否是工具函数
        """
        # 必须是函数
        if not inspect.isfunction(obj):
            return False
        
        # 跳过私有函数
        if name.startswith('_'):
            return False
        
        # 跳过特殊方法
        if name.startswith('__') and name.endswith('__'):
            return False
        
        return True
    
    def _file_to_module(self, py_file: Path) -> str:
        """
        将文件路径转换为模块名
        
        Args:
            py_file: Python 文件路径
        
        Returns:
            模块名
        """
        # 获取相对路径
        rel_path = py_file.with_suffix('')
        
        # 转换为模块名
        module_name = str(rel_path).replace('/', '.').replace('\\', '.')
        
        return module_name


def scan_tools():
    """
    扫描工具的便捷函数
    
    使用示例:
        from utils.evolution.scanner import scan_tools
        scan_tools()
    """
    scanner = ToolScanner()
    scanner.scan_all()


if __name__ == "__main__":
    # 直接运行此文件进行扫描
    scan_tools()