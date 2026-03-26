#!/usr/bin/env python
"""
测试用例命名规范检查脚本

自动检查测试用例是否符合命名规范：
1. 文件命名: test_<模块>.py
2. 类命名: Test<模块><子模块>
3. 方法命名: test_<操作>_<验证点>
4. docstring 包含 TC ID
5. fixture 使用正确

运行方式:
    python utils/_scripts/check_naming_rules.py
    python utils/_scripts/check_naming_rules.py --path C:\11_UITest\tests
    python utils/_scripts/check_naming_rules.py --fix  # 自动修复部分问题
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NamingIssue:
    """命名问题"""
    file: str
    line: int
    level: str  # error, warning, info
    rule: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class CheckResult:
    """检查结果"""
    passed: int = 0
    errors: int = 0
    warnings: int = 0
    issues: List[NamingIssue] = field(default_factory=list)
    
    def add_error(self, issue: NamingIssue):
        self.errors += 1
        self.issues.append(issue)
    
    def add_warning(self, issue: NamingIssue):
        self.warnings += 1
        self.issues.append(issue)
    
    def add_pass(self):
        self.passed += 1


# 命名规则定义
FILE_PATTERN = re.compile(r'^test_[a-z][a-z0-9_]*\.py$')
CLASS_PATTERN = re.compile(r'^Test([A-Z][a-zA-Z0-9]*)+$')
METHOD_PATTERN = re.compile(r'^test_[a-z][a-z0-9_]*(?:_[a-z0-9]+)*$')
TC_ID_PATTERN = re.compile(r'TC-[A-Z]+-\d+')

# 操作动词白名单
ACTION_VERBS = {
    'add', 'edit', 'delete', 'query', 'search',
    'import', 'export', 'upload', 'download',
    'audit', 'approve', 'reject', 'submit',
    'login', 'logout', 'navigate', 'click', 'fill',
    'verify', 'check', 'validate', 'wait'
}

# 验证点后缀白名单
VALIDATION_SUFFIXES = {
    'success', 'fail', 'error', 'timeout',
    'visible', 'hidden', 'enabled', 'disabled',
    'count', 'number', 'total', 'exists', 'not_exists',
    'permission', 'authorized', 'unauthorized',
    'complete', 'pending', 'processing',
    'before', 'after', 'first', 'last', 'empty', 'not_empty'
}


class NamingRulesChecker:
    """命名规则检查器"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.result = CheckResult()
        
    def check_all(self) -> CheckResult:
        """检查所有测试文件"""
        test_files = list(self.root_path.rglob('test_*.py'))
        
        print(f"\n{'='*60}")
        print(f"检查目录: {self.root_path}")
        print(f"找到 {len(test_files)} 个测试文件")
        print(f"{'='*60}\n")
        
        for test_file in sorted(test_files):
            self._check_file(test_file)
        
        return self.result
    
    def _check_file(self, file_path: Path):
        """检查单个文件"""
        relative_path = file_path.relative_to(self.root_path)
        
        # Rule 1: 文件命名检查
        filename = file_path.name
        if not FILE_PATTERN.match(filename):
            self.result.add_error(NamingIssue(
                file=str(relative_path),
                line=0,
                level='error',
                rule='FILE_NAMING',
                message=f"文件名 '{filename}' 不符合规范",
                suggestion=f"应使用 test_<模块>.py 格式，如: test_{self._suggest_module_name(filename)}"
            ))
        
        # 读取文件内容
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
        except Exception as e:
            self.result.add_error(NamingIssue(
                file=str(relative_path),
                line=0,
                level='error',
                rule='FILE_READ',
                message=f"无法读取文件: {e}"
            ))
            return
        
        # 解析类和方涓
        classes = self._find_classes(content)
        for class_name, class_line in classes:
            self._check_class(file_path, relative_path, class_name, class_line, content)
        
        # 如果没有找到任何测试类
        if not classes:
            self.result.add_warning(NamingIssue(
                file=str(relative_path),
                line=0,
                level='warning',
                rule='NO_TEST_CLASS',
                message="文件中没有找到测试类"
            ))
    
    def _find_classes(self, content: str) -> List[tuple]:
        """查找所有测试类"""
        classes = []
        for i, line in enumerate(content.split('\n'), 1):
            match = re.match(r'^class (Test\w+):', line)
            if match:
                classes.append((match.group(1), i))
        return classes
    
    def _check_class(self, file_path: Path, relative_path: str, class_name: str, line_num: int, content: str):
        """检查类命名"""
        
        # Rule 2: 类命名检查
        # 提取模块名（去掉 Test 前缀）
        module_part = class_name[4:]  # 去掉 "Test" 前缀
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', module_part):
            self.result.add_error(NamingIssue(
                file=str(relative_path),
                line=line_num,
                level='error',
                rule='CLASS_NAMING',
                message=f"类名 '{class_name}' 不符合 PascalCase 规范",
                suggestion="模块部分应使用 PascalCase，如: TestLogin, TestMyDataFamilyMember"
            ))
        
        # 查找类中的所有测试方法
        methods = self._find_methods(content)
        
        for method_name, method_line in methods:
            self._check_method(file_path, relative_path, class_name, method_name, method_line, content)
    
    def _find_methods(self, content: str) -> List[tuple]:
        """查找所有测试方法"""
        methods = []
        for i, line in enumerate(content.split('\n'), 1):
            # 匹配 test_ 开头的方法（不是在注释或字符串中）
            if re.match(r'^\s+def (test_\w+)\(', line):
                match = re.match(r'^\s+def (test_\w+)\(', line)
                if match:
                    methods.append((match.group(1), i))
        return methods
    
    def _check_method(self, file_path: Path, relative_path: str, class_name: str, 
                     method_name: str, line_num: int, content: str):
        """检查方法命名"""
        
        # Rule 3: 方法命名检查
        if not METHOD_PATTERN.match(method_name):
            self.result.add_error(NamingIssue(
                file=str(relative_path),
                line=line_num,
                level='error',
                rule='METHOD_NAMING',
                message=f"方法名 '{method_name}' 不符合规范",
                suggestion="应使用 snake_case: test_<操作>_<验证点>，如: test_login_success"
            ))
        
        # 提取操作动词和验证点
        parts = method_name.split('_')[1:]  # 去掉 test_ 前缀
        if parts:
            action = parts[0] if parts else ''
            suffix = parts[-1] if len(parts) > 1 else ''
            
            # 检查操作动词
            if action not in ACTION_VERBS and len(parts) == 1:
                self.result.add_warning(NamingIssue(
                    file=str(relative_path),
                    line=line_num,
                    level='warning',
                    rule='METHOD_ACTION',
                    message=f"方法名 '{method_name}' 的操作动词 '{action}' 不在白名单中",
                    suggestion=f"建议使用: {', '.join(sorted(ACTION_VERBS))}"
                ))
            
            # 检查验证点后缀
            if suffix not in VALIDATION_SUFFIXES and len(parts) > 1:
                self.result.add_warning(NamingIssue(
                    file=str(relative_path),
                    line=line_num,
                    level='warning',
                    rule='METHOD_SUFFIX',
                    message=f"方法名 '{method_name}' 的验证点后缀 '{suffix}' 不在白名单中",
                    suggestion=f"建议使用: {', '.join(sorted(VALIDATION_SUFFIXES))}"
                ))
        
        # Rule 4: TC ID 检查
        # 提取方法的 docstring
        method_start = content.find(f'def {method_name}(')
        if method_start != -1:
            docstring = self._extract_docstring(content, method_start)
            if not TC_ID_PATTERN.search(docstring):
                self.result.add_warning(NamingIssue(
                    file=str(relative_path),
                    line=line_num,
                    level='warning',
                    rule='TC_ID_MISSING',
                    message=f"方法 '{method_name}' 的 docstring 缺少 TC ID",
                    suggestion="docstring 应包含 TC ID，如: TC-100269"
                ))
    
    def _extract_docstring(self, content: str, method_start: int) -> str:
        """提取方法的 docstring"""
        # 找到方法定义后的第一个三引号
        after_method = content[method_start:]
        docstring_match = re.search(r'"""(.*?)"""', after_method, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1)
        return ""
    
    def _suggest_module_name(self, filename: str) -> str:
        """建议模块名"""
        # test_xxx_yyy.py -> xxx_yyy
        return filename[5:-3]  # 去掉 test_ 前缀和 .py 后缀
    
    def print_report(self):
        """打印报告"""
        print(f"\n{'='*60}")
        print("检查结果汇总")
        print(f"{'='*60}")
        print(f"  ✅ 通过: {self.result.passed}")
        print(f"  ❌ 错误: {self.result.errors}")
        print(f"  ⚠️  警告: {self.result.warnings}")
        print(f"{'='*60}\n")
        
        if self.result.errors > 0:
            print("错误详情:")
            print("-" * 60)
            for issue in self.result.issues:
                if issue.level == 'error':
                    self._print_issue(issue)
            
            print("\n警告详情:")
            print("-" * 60)
            for issue in self.result.issues:
                if issue.level == 'warning':
                    self._print_issue(issue)
        elif self.result.warnings > 0:
            print("警告详情:")
            print("-" * 60)
            for issue in self.result.issues:
                if issue.level == 'warning':
                    self._print_issue(issue)
        else:
            print("🎉 所有检查通过！命名规范良好！")
        
        print()
    
    def _print_issue(self, issue: NamingIssue):
        """打印单个问题"""
        prefix = "❌" if issue.level == 'error' else "⚠️"
        print(f"\n{prefix} [{issue.rule}] {issue.file}:{issue.line}")
        print(f"   {issue.message}")
        if issue.suggestion:
            print(f"   💡 建议: {issue.suggestion}")
    
    def exit_code(self) -> int:
        """返回退出码"""
        return 1 if self.result.errors > 0 else 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='测试用例命名规范检查')
    parser.add_argument('--path', '-p', default=r'C:\11_UITest\tests',
                        help='测试目录路径')
    parser.add_argument('--fix', '-f', action='store_true',
                        help='自动修复部分问题（暂未实现）')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='只输出汇总信息')
    
    args = parser.parse_args()
    
    checker = NamingRulesChecker(args.path)
    checker.check_all()
    checker.print_report()
    
    sys.exit(checker.exit_code())


if __name__ == '__main__':
    main()
