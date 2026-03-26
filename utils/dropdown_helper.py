"""
通用下拉选择工具

支持多种下拉类型：
- 单选下拉 (Select)
- 多选下拉 (Multi-Select)
- 下拉树 (TreeSelect)

使用策略模式，根据下拉类型自动选择处理方式
"""
import time
from typing import List, Optional, Union, Callable
from enum import Enum


class DropdownType(Enum):
    """下拉类型枚举"""
    SINGLE = "single"      # 单选下拉
    MULTI = "multi"       # 多选下拉
    TREE = "tree"         # 下拉树


class DropdownOption:
    """下拉选项"""
    def __init__(self, text: str, value: str = None, disabled: bool = False):
        self.text = text
        self.value = value or text
        self.disabled = disabled


class DropdownHelper:
    """
    通用下拉选择助手
    
    使用方法:
        helper = DropdownHelper(page)
        
        # 单选：选择指定文本
        helper.select("父亲", selector="input[placeholder='请选择']")
        
        # 单选：选择不同的选项（用于编辑场景）
        helper.select_different("母亲", selector="input[placeholder='请选择']")
        
        # 单选：随机选择（用于新增场景）
        helper.select_random(selector="input[placeholder='请选择']")
        
        # 多选：选择多个
        helper.select_multiple(["父亲", "母亲"], selector="input[placeholder='请选择']")
        
        # 下拉树：选择节点
        helper.select_tree("北京市/海淀区", selector="input[placeholder='请选择']")
    """
    
    def __init__(self, page):
        self.page = page
    
    def _find_options(self) -> List[DropdownOption]:
        """查找所有可见的选项"""
        result = self.page.evaluate("""
            () => {
                const items = document.querySelectorAll('li, .ant-select-dropdown-menu-item, .rc-select-dropdown-menu-item');
                const options = [];
                for (let item of items) {
                    if (item.offsetParent !== null) {  // 只取可见的
                        options.push({
                            text: item.textContent.trim(),
                            value: item.getAttribute('data-value') || item.textContent.trim(),
                            disabled: item.classList.contains('ant-select-dropdown-menu-item-disabled') || 
                                     item.classList.contains('rc-select-dropdown-menu-item-disabled')
                        });
                    }
                }
                return options;
            }
        """)
        return [DropdownOption(**r) for r in result]
    
    def _find_tree_nodes(self) -> List[DropdownOption]:
        """查找下拉树的所有节点"""
        result = self.page.evaluate("""
            () => {
                const nodes = document.querySelectorAll('.ant-tree-treenode, .rc-tree-select-treenode, [role="treeitem"]');
                const options = [];
                for (let node of nodes) {
                    const title = node.querySelector('.ant-tree-title, .rc-tree-select-node-title, [role="treeitem"] span');
                    if (title) {
                        options.push({
                            text: title.textContent.trim(),
                            value: node.getAttribute('data-key') || node.getAttribute('key') || title.textContent.trim(),
                            disabled: node.classList.contains('ant-tree-node-disabled') || 
                                     node.classList.contains('rc-tree-select-node-disabled')
                        });
                    }
                }
                return options;
            }
        """)
        return [DropdownOption(**r) for r in result if r.get('text')]
    
    def _click_option(self, option: DropdownOption) -> bool:
        """点击选项"""
        try:
            result = self.page.evaluate("""
                (optionText) => {
                    // 尝试多种选择器
                    const selectors = [
                        `li[title="${optionText}"]`,
                        `li:has-text("${optionText}")`,
                        `.ant-select-dropdown-menu-item:has-text("${optionText}")`,
                        `.rc-select-dropdown-menu-item:has-text("${optionText}")`,
                        `[data-value="${optionText}"]`
                    ];
                    
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent !== null) {
                            el.click();
                            return { success: true, text: optionText };
                        }
                    }
                    return { success: false };
                }
            """, option.text)
            
            if result.get('success'):
                print(f"  [Dropdown] Selected: {option.text}")
                return True
            return False
        except Exception as e:
            print(f"  [Dropdown] Click failed: {e}")
            return False
    
    # ==================== 公开方法 ====================
    
    def select(self, text: str, selector: str = None, dropdown_type: DropdownType = DropdownType.SINGLE) -> bool:
        """
        选择指定文本的选项
        
        Args:
            text: 要选择的选项文本
            selector: 下拉框选择器（可选）
            dropdown_type: 下拉类型
            
        Returns:
            bool: 选择成功返回 True
        """
        if selector:
            self.page.locator(selector).click()
            time.sleep(0.3)
        
        if dropdown_type == DropdownType.TREE:
            options = self._find_tree_nodes()
        else:
            options = self._find_options()
        
        for opt in options:
            if text in opt.text and not opt.disabled:
                return self._click_option(opt)
        
        print(f"  [Dropdown] Option not found: {text}")
        return False
    
    def select_different(self, current_text: str, selector: str = None, 
                         dropdown_type: DropdownType = DropdownType.SINGLE) -> Optional[str]:
        """
        选择与当前值不同的选项（用于编辑场景）
        
        Args:
            current_text: 当前已选中的文本
            selector: 下拉框选择器
            
        Returns:
            str: 选中的新文本，失败返回 None
        """
        if selector:
            self.page.locator(selector).click()
            time.sleep(0.3)
        
        if dropdown_type == DropdownType.TREE:
            options = self._find_tree_nodes()
        else:
            options = self._find_options()
        
        for opt in options:
            if opt.text != current_text and not opt.disabled and opt.text.strip():
                self._click_option(opt)
                return opt.text
        
        print(f"  [Dropdown] No different option found (current: {current_text})")
        return None
    
    def select_random(self, selector: str = None, exclude: List[str] = None,
                     dropdown_type: DropdownType = DropdownType.SINGLE) -> Optional[str]:
        """
        随机选择一个选项（用于新增场景）
        
        Args:
            selector: 下拉框选择器
            exclude: 要排除的选项列表
            dropdown_type: 下拉类型
            
        Returns:
            str: 选中的文本，失败返回 None
        """
        import random
        
        if selector:
            self.page.locator(selector).click()
            time.sleep(0.3)
        
        if dropdown_type == DropdownType.TREE:
            options = self._find_tree_nodes()
        else:
            options = self._find_options()
        
        exclude = exclude or []
        available = [opt for opt in options if not opt.disabled and opt.text not in exclude]
        
        if not available:
            print(f"  [Dropdown] No available options")
            return None
        
        chosen = random.choice(available)
        self._click_option(chosen)
        return chosen.text
    
    def select_by_index(self, index: int, selector: str = None,
                        dropdown_type: DropdownType = DropdownType.SINGLE) -> Optional[str]:
        """
        通过索引选择选项
        
        Args:
            index: 选项索引（从0开始）
            selector: 下拉框选择器
            
        Returns:
            str: 选中的文本，失败返回 None
        """
        if selector:
            self.page.locator(selector).click()
            time.sleep(0.3)
        
        if dropdown_type == DropdownType.TREE:
            options = self._find_tree_nodes()
        else:
            options = self._find_options()
        
        if 0 <= index < len(options):
            opt = options[index]
            if not opt.disabled:
                self._click_option(opt)
                return opt.text
        
        print(f"  [Dropdown] Index out of range: {index}")
        return None
    
    def select_multiple(self, texts: List[str], selector: str = None) -> bool:
        """
        多选：选择多个选项
        
        Args:
            texts: 要选择的选项文本列表
            selector: 下拉框选择器
            
        Returns:
            bool: 全部选择成功返回 True
        """
        if selector:
            self.page.locator(selector).click()
            time.sleep(0.3)
        
        options = self._find_options()
        success = True
        
        for text in texts:
            found = False
            for opt in options:
                if text in opt.text and not opt.disabled:
                    self._click_option(opt)
                    time.sleep(0.2)
                    found = True
                    break
            if not found:
                print(f"  [Dropdown] Not found: {text}")
                success = False
        
        return success
    
    def get_current_value(self, selector: str = None) -> Optional[str]:
        """
        获取当前选中的值
        
        Args:
            selector: 下拉框选择器
            
        Returns:
            str: 当前选中的文本
        """
        try:
            if selector:
                return self.page.locator(selector).input_value() or self.page.locator(selector).text_content()
            return None
        except:
            return None
    
    def get_all_options(self, selector: str = None, 
                        dropdown_type: DropdownType = DropdownType.SINGLE) -> List[str]:
        """
        获取所有可用选项
        
        Args:
            selector: 下拉框选择器
            dropdown_type: 下拉类型
            
        Returns:
            list: 选项文本列表
        """
        if selector:
            self.page.locator(selector).click()
            time.sleep(0.3)
        
        if dropdown_type == DropdownType.TREE:
            options = self._find_tree_nodes()
        else:
            options = self._find_options()
        
        return [opt.text for opt in options if not opt.disabled]


# 便捷函数（保持向后兼容）
def select_dropdown_option(page, dropdown_selector: str, option_text: str, timeout: int = 5000) -> bool:
    """兼容旧接口"""
    helper = DropdownHelper(page)
    return helper.select(option_text, dropdown_selector)


def select_dropdown_by_index(page, dropdown_selector: str, index: int = 0) -> bool:
    """兼容旧接口"""
    helper = DropdownHelper(page)
    return helper.select_by_index(index, dropdown_selector) is not None


def open_dropdown_and_get_options(page, dropdown_selector: str) -> list:
    """兼容旧接口"""
    helper = DropdownHelper(page)
    return helper.get_all_options(dropdown_selector)
