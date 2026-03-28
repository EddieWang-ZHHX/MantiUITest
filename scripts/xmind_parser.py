"""XMind 测试用例解析工具 v3

支持格式：
- XMind 8/2020 (ZIP + content.xml)

使用方法：
    from utils.xmind_parser import XMindParser, parse_xmind
    
    parser = XMindParser("path/to/test.xmind")
    cases = parser.parse()
    
    # 统计
    summary = parser.to_summary(cases)
    print(f\"P1: {summary['p1']}, P2: {summary['p2']}, P3: {summary['p3']}\")
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import re


@dataclass
class TestCase:
    """测试用例数据类"""
    id: str
    name: str
    priority: str  # P1, P2, P3
    module: str
    steps: List[str]
    expected: List[str]
    status: str = "active"  # active, deprecated
    prerequisites: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class XMindParser:
    """XMind 测试用例解析器 v3"""
    
    # 命名空间
    NS = 'urn:xmind:xmap:xmlns:content:2.0'
    
    def __init__(self, xmind_path: str):
        self.xmind_path = Path(xmind_path)
        if not self.xmind_path.exists():
            raise FileNotFoundError(f"XMind 文件不存在: {xmind_path}")
    
    def parse(self) -> List[TestCase]:
        """解析 XMind 文件"""
        cases = []
        
        with zipfile.ZipFile(self.xmind_path, 'r') as zf:
            with zf.open('content.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
            
            # 递归解析
            cases = self._extract_all(root, module_stack=[])
        
        return cases
    
    def _get_title(self, elem: ET.Element) -> Optional[str]:
        """获取标题"""
        # 处理命名空间
        for child in elem:
            if child.tag.endswith('}title') or child.tag == 'title':
                return child.text
        return None
    
    def _extract_all(self, elem: ET.Element, module_stack: List[str]) -> List[TestCase]:
        """递归提取所有测试用例"""
        cases = []
        
        title = self._get_title(elem)
        if title:
            # 检查是否是测试用例 (tc- 开头)
            if title.lower().startswith('tc-'):
                case = self._parse_case(elem, module_stack)
                if case:
                    cases.append(case)
            else:
                # 作为模块处理
                module_stack = module_stack + [title]
        
        # 递归处理所有子元素
        for child in elem:
            cases.extend(self._extract_all(child, module_stack))
        
        return cases
    
    def _parse_case(self, topic: ET.Element, module_stack: List[str]) -> Optional[TestCase]:
        """解析单个测试用例"""
        title = self._get_title(topic) or ""
        
        # 提取 ID
        case_id = self._extract_id(title)
        
        # 提取名称和优先级
        name, priority = self._extract_name_priority(title)
        
        # 提取步骤和预期结果
        steps, expected = self._extract_steps(topic)
        
        # 检查是否废弃
        tags = self._extract_tags(topic)
        status = "deprecated" if "废弃" in tags else "active"
        
        # 获取模块
        module = "/".join(module_stack) if module_stack else "Unknown"
        
        return TestCase(
            id=case_id or title,
            name=name,
            priority=priority,
            module=module,
            steps=steps,
            expected=expected,
            status=status,
            tags=tags
        )
    
    def _extract_id(self, title: str) -> Optional[str]:
        """从标题提取用例 ID"""
        match = re.search(r'(TC-\d+|id:\d+)', title, re.IGNORECASE)
        return match.group(0).upper() if match else None
    
    def _extract_name_priority(self, title: str) -> tuple:
        """提取用例名称和优先级"""
        # 匹配 tc-P1: 格式
        match = re.match(r'(?i)tc-(P\d+):(.+)', title)
        if match:
            return match.group(2).strip(), match.group(1).upper()
        
        # 从标题提取 P1/P2/P3
        priority_match = re.search(r'\[?(P[123])\]?', title, re.IGNORECASE)
        priority = priority_match.group(1).upper() if priority_match else "P3"
        
        # 清理名称
        name = re.sub(r'\[?P[123]\]?:?\s*', '', title, flags=re.IGNORECASE).strip()
        
        return name, priority
    
    def _extract_steps(self, topic: ET.Element) -> tuple:
        """提取测试步骤和预期结果
        
        结构：
        - 步骤 (以数字开头，如 "1. xxx")
          - 步骤的子主题 = 预期结果
        """
        steps = []
        expected = []
        
        # 递归查找所有 topic
        def process_topic(elem):
            for child in elem:
                child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                if child_tag == 'topic':
                    title = self._get_title(child)
                    if title:
                        # 以数字开头的是步骤
                        if re.match(r'^\d+[\..、\s]', title.strip()):
                            steps.append(title.strip())
                            
                            # 查找这个步骤的子主题（预期结果）
                            for subchild in child:
                                subchild_tag = subchild.tag.split('}')[-1] if '}' in subchild.tag else subchild.tag
                                if subchild_tag == 'children':
                                    for topics in subchild:
                                        topics_tag = topics.tag.split('}')[-1] if '}' in topics.tag else topics.tag
                                        if topics_tag == 'topics':
                                            for step_topic in topics:
                                                step_title = self._get_title(step_topic)
                                                if step_title:
                                                    expected.append(step_title)
                
                # 继续递归
                process_topic(child)
        
        process_topic(topic)
        return steps, expected
    
    def _extract_tags(self, topic: ET.Element) -> List[str]:
        """提取标签"""
        tags = []
        
        def find_tags(elem):
            for child in elem:
                title = self._get_title(child)
                if title and title.startswith('tag:'):
                    tag_content = title[4:].strip()
                    if tag_content:
                        tags.append(tag_content)
                find_tags(child)
        
        find_tags(topic)
        return tags
    
    def to_json(self, cases: List[TestCase], pretty: bool = True) -> str:
        """转换为 JSON"""
        data = [c.to_dict() for c in cases]
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    
    def to_markdown(self, cases: List[TestCase]) -> str:
        """转换为 Markdown"""
        lines = ["# 测试用例列表\n"]
        
        current_module = None
        for case in cases:
            if case.module != current_module:
                current_module = case.module
                lines.append(f"\n## {current_module}\n")
            
            icon = "🔴" if case.priority == "P1" else "🟡" if case.priority == "P2" else "🟢"
            status_icon = " ❌ 废弃" if case.status == "deprecated" else ""
            
            lines.append(f"### {icon} {case.name} ({case.id}){status_icon}\n")
            lines.append(f"**优先级**: {case.priority} | **状态**: {case.status}\n")
            
            if case.steps:
                lines.append("**步骤**:\n")
                for step in case.steps:
                    lines.append(f"- {step}\n")
            
            if case.expected:
                lines.append("**预期**:\n")
                for e in case.expected:
                    lines.append(f"- {e}\n")
            
            lines.append("\n")
        
        return ''.join(lines)
    
    def to_summary(self, cases: List[TestCase]) -> Dict[str, Any]:
        """生成摘要统计"""
        total = len(cases)
        p1 = sum(1 for c in cases if c.priority == "P1")
        p2 = sum(1 for c in cases if c.priority == "P2")
        p3 = sum(1 for c in cases if c.priority == "P3")
        deprecated = sum(1 for c in cases if c.status == "deprecated")
        
        modules = {}
        for c in cases:
            if c.module not in modules:
                modules[c.module] = {"total": 0, "p1": 0, "p2": 0, "p3": 0, "deprecated": 0}
            modules[c.module]["total"] += 1
            if c.priority == "P1":
                modules[c.module]["p1"] += 1
            elif c.priority == "P2":
                modules[c.module]["p2"] += 1
            else:
                modules[c.module]["p3"] += 1
            if c.status == "deprecated":
                modules[c.module]["deprecated"] += 1
        
        return {
            "total": total,
            "p1": p1,
            "p2": p2,
            "p3": p3,
            "deprecated": deprecated,
            "active": total - deprecated,
            "modules": modules
        }


def parse_xmind(xmind_path: str) -> List[TestCase]:
    """解析 XMind 文件"""
    parser = XMindParser(xmind_path)
    return parser.parse()


def export_xmind(xmind_path: str, output_path: str, format: str = 'json'):
    """解析并导出 XMind"""
    parser = XMindParser(xmind_path)
    cases = parser.parse()
    
    output = Path(output_path)
    
    if format == 'json':
        content = parser.to_json(cases)
        output.write_text(content, encoding='utf-8')
    elif format == 'markdown':
        content = parser.to_markdown(cases)
        output.write_text(content, encoding='utf-8')
    else:
        raise ValueError(f"不支持的格式: {format}")
    
    return len(cases)
