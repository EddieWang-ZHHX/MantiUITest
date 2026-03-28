"""
工具进化监控装饰器

使用方式：
@evolution_monitor("my_tool")
def my_tool(arg1: str) -> dict:
    ...

装饰器会自动：
1. 注册工具
2. 监控执行结果
3. 记录失败上下文
4. 触发进化流程
"""

from functools import wraps
import inspect
from loguru import logger


def evolution_monitor(name: str = None):
    """
    工具进化监控装饰器
    
    Args:
        name: 工具名称（可选，默认使用函数名）
    
    使用示例：
        @evolution_monitor("page_analyzer.analyze")
        def analyze(page_content: str) -> dict:
            ...
    """
    def decorator(func):
        # 确定工具名称
        tool_name = name or func.__name__
        
        # 获取工具信息
        module = inspect.getmodule(func).__name__ if inspect.getmodule(func) else "unknown"
        file_path = inspect.getfile(func)
        
        # 延迟导入避免循环依赖
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 延迟导入（避免循环依赖）
            from utils.evolution.registry import ToolRegistry
            
            registry = ToolRegistry()
            
            # 自动注册
            registry.register(tool_name, module, file_path)
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 记录成功
                registry.record_execution(tool_name, True, {
                    'args': _safe_str(args, 200),
                    'kwargs': _safe_str(kwargs, 200)
                })
                
                return result
                
            except Exception as e:
                # 记录失败
                registry.record_execution(tool_name, False, {
                    'args': _safe_str(args, 200),
                    'kwargs': _safe_str(kwargs, 200),
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                
                # 重新抛出异常
                raise
        
        return wrapper
    
    return decorator


def _safe_str(obj, max_length: int = 200) -> str:
    """
    安全转换为字符串，限制长度
    
    Args:
        obj: 对象
        max_length: 最大长度
    
    Returns:
        字符串
    """
    try:
        s = str(obj)
        if len(s) > max_length:
            return s[:max_length] + "..."
        return s
    except Exception:
        return "<无法序列化>"