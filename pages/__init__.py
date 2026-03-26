"""页面对象自动发现系统

设计原则：
1. 启动时自动发现 pages/ 目录下的所有页面对象
2. 支持多层级目录结构
3. 兼容 CI/CD - 无状态，可重复执行
4. 延迟加载 - 提升启动速度

使用方法：
    from pages import get_page
    
    # 获取页面对象（延迟加载）
    login_page = get_page("login")
    
    # 列出所有可用页面
    from pages import list_pages
    print(list_pages())
"""

import os
import re
from pathlib import Path
from typing import Dict, Type, Optional, List

# 全局页面池 (类级别，非实例)
_PAGE_REGISTRY: Dict[str, Type] = {}
_INITIALIZED = False


class PageRegistry:
    """页面对象注册表"""
    
    @staticmethod
    def register(name: str, page_class: Type) -> None:
        """注册页面对象
        
        Args:
            name: 页面名称 (如 "login", "my_data")
            page_class: 页面类 (必须是 BasePage 的子类)
        """
        if not name:  # 跳过空名称
            return
        _PAGE_REGISTRY[name.lower()] = page_class
    
    @staticmethod
    def get(name: str) -> Type:
        """获取页面对象类
        
        Args:
            name: 页面名称
            
        Returns:
            页面类
            
        Raises:
            ValueError: 页面不存在
        """
        name_lower = name.lower()
        if name_lower not in _PAGE_REGISTRY:
            available = list(_PAGE_REGISTRY.keys())
            raise ValueError(
                f"Unknown page: '{name}'. Available pages: {available}"
            )
        return _PAGE_REGISTRY[name_lower]
    
    @staticmethod
    def list_all() -> List[str]:
        """列出所有已注册的页面"""
        return sorted(_PAGE_REGISTRY.keys())
    
    @staticmethod
    def is_registered(name: str) -> bool:
        """检查页面是否已注册"""
        return name.lower() in _PAGE_REGISTRY
    
    @staticmethod
    def clear() -> None:
        """清空注册表 (主要用于测试)"""
        _PAGE_REGISTRY.clear()


def _discover_pages() -> None:
    """自动发现并注册所有页面对象
    
    扫描规则：
    1. 扫描 pages/ 目录下所有 *_page.py 文件
    2. 跳过以 _ 开头的文件
    3. 从类名提取页面名称 (XxxPage -> xxx)
    4. 类必须是 BasePage 的子类（且不是 BasePage 本身）
    """
    global _INITIALIZED
    
    if _INITIALIZED:
        return
    
    # 延迟导入避免循环依赖
    from pages.base_page import BasePage
    
    # 获取 pages 目录
    pages_dir = Path(__file__).parent
    
    # 遍历所有 *_page.py 文件
    for py_file in pages_dir.rglob("*_page.py"):
        # 跳过以 _ 开头的文件
        if py_file.name.startswith("_"):
            continue
        
        # 构建模块名
        rel_path = py_file.relative_to(pages_dir.parent)
        module_parts = list(rel_path.parts[:-1]) + [py_file.stem]
        module_name = ".".join(module_parts)
        
        try:
            # 动态导入模块
            import importlib
            module = importlib.import_module(module_name)
            
            # 查找页面类
            for attr_name in dir(module):
                if not attr_name.endswith("Page"):
                    continue
                    
                attr = getattr(module, attr_name)
                
                # 必须是类，不是实例
                if not isinstance(attr, type):
                    continue
                
                # 必须是 BasePage 的子类
                try:
                    if not issubclass(attr, BasePage):
                        continue
                except TypeError:
                    # issubclass() 的第一个参数不是类
                    continue
                
                # 跳过 BasePage 本身
                if attr.__name__ == "BasePage":
                    continue
                
                # 跳过 Playwright 的 Page 类（避免与 BasePage.Page 属性冲突）
                if attr.__name__ == "Page":
                    continue
                
                # 提取页面名称
                # "LoginPage" -> "login"
                # "MyDataPage" -> "my_data"
                # "TeacherDataCenterPage" -> "teacher_data_center"
                page_name = _camel_to_snake(attr_name[:-4])  # 移除 "Page" 后缀并转换命名风格
                
                # 跳过空名称
                if not page_name:
                    continue
                
                # 注册
                _PAGE_REGISTRY[page_name] = attr
                
        except Exception as e:
            # CI/CD 环境不能因为页面发现问题导致整个测试失败
            # 只记录警告，不中断执行
            import sys
            print(f"Warning: Failed to load page module '{module_name}': {e}", file=sys.stderr)
    
    _INITIALIZED = True


def _camel_to_snake(name: str) -> str:
    """将 CamelCase 转换为 snake_case
    
    Examples:
        LoginPage -> login
        MyDataPage -> my_data
        TeacherDataCenterPage -> teacher_data_center
    """
    # 插入下划线并转为小写
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_page(name: str) -> Type:
    """获取页面对象类 (延迟加载)
    
    Args:
        name: 页面名称
        
    Returns:
        页面类 (需要实例化)
        
    Example:
        from pages import get_page
        
        # 获取页面类
        LoginPage = get_page("login")
        
        # 实例化
        login_page = LoginPage(page)
        
        # 使用
        login_page.navigate_to()
    """
    _discover_pages()
    return PageRegistry.get(name)


def list_pages() -> List[str]:
    """列出所有可用的页面名称"""
    _discover_pages()
    return PageRegistry.list_all()


def create_page(name: str, page_instance, base_url: str = "") -> object:
    """创建页面对象实例
    
    Args:
        name: 页面名称
        page_instance: Playwright page 实例
        base_url: 基础 URL
        
    Returns:
        页面对象实例
    """
    page_class = get_page(name)
    return page_class(page_instance, base_url)


# 启动时自动发现
_discover_pages()
