"""测试结果格式化工具

支持多种输出格式，便于 CI/CD 集成：
- JSON: 机器可读，用于数据交换
- JUnit XML: CI/CD 系统兼容 (Jenkins, GitLab CI, GitHub Actions)
- Table: 人类可读
- CSV: 数据分析

设计原则：
1. 无状态函数，可重复调用
2. 支持流水线处理
3. CI/CD 友好 - 稳定输出，不依赖终端
"""

import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TestResult:
    """测试结果数据类"""
    name: str
    status: str  # passed, failed, skipped, error
    duration: float  # 秒
    message: Optional[str] = None
    traceback: Optional[str] = None
    test_class: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class TestResultFormatter:
    """测试结果格式化器"""
    
    @staticmethod
    def to_json(results: List[TestResult], pretty: bool = False) -> str:
        """转换为 JSON 格式
        
        Args:
            results: 测试结果列表
            pretty: 是否格式化输出
            
        Returns:
            JSON 字符串
        """
        data = [asdict(r) for r in results]
        
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    
    @staticmethod
    def to_junit_xml(results: List[TestResult], 
                     name: str = "UITestSuite",
                     package: str = "ui.tests") -> str:
        """转换为 JUnit XML 格式
        
        用于 CI/CD 系统：
        - Jenkins
        - GitLab CI
        - GitHub Actions
        - CircleCI
        
        Args:
            results: 测试结果列表
            name: 测试套件名称
            package: 包路径
            
        Returns:
            JUnit XML 字符串
        """
        total_time = sum(r.duration for r in results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")
        
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<testsuite name="{name}" tests="{len(results)}" '
            f'failures="{failed}" errors="{errors}" skipped="{skipped}" '
            f'time="{total_time:.3f}" timestamp="{datetime.now().isoformat()}">'
        ]
        
        for r in results:
            # 转义 XML 特殊字符
            test_name = _xml_escape(r.name)
            class_name = _xml_escape(r.test_class or "unknown")
            message = _xml_escape(r.message or "")
            traceback = _xml_escape(r.traceback or "")
            
            if r.status == "failed":
                lines.append(
                    f'  <testcase classname="{class_name}" name="{test_name}" '
                    f'time="{r.duration:.3f}">'
                )
                lines.append(f'    <failure message="{message}">{traceback}</failure>')
                lines.append('  </testcase>')
            elif r.status == "error":
                lines.append(
                    f'  <testcase classname="{class_name}" name="{test_name}" '
                    f'time="{r.duration:.3f}">'
                )
                lines.append(f'    <error message="{message}">{traceback}</error>')
                lines.append('  </testcase>')
            elif r.status == "skipped":
                lines.append(
                    f'  <testcase classname="{class_name}" name="{test_name}" '
                    f'time="{r.duration:.3f}">'
                )
                lines.append('    <skipped/>')
                lines.append('  </testcase>')
            else:
                lines.append(
                    f'  <testcase classname="{class_name}" name="{test_name}" '
                    f'time="{r.duration:.3f}"/>'
                )
        
        lines.append('</testsuite>')
        return '\n'.join(lines)
    
    @staticmethod
    def to_table(results: List[TestResult]) -> str:
        """转换为表格格式
        
        人类可读，用于本地调试
        
        Args:
            results: 测试结果列表
            
        Returns:
            表格字符串
        """
        if not results:
            return "No test results"
        
        # 表头
        lines = [
            f"{'Status':<10} {'Duration':<10} {'Test Name':<50}",
            "-" * 70
        ]
        
        # 数据行
        for r in results:
            status_icon = {
                "passed": "✅ PASS",
                "failed": "❌ FAIL",
                "skipped": "⏭️  SKIP",
                "error": "💥 ERROR"
            }.get(r.status, r.status.upper())
            
            lines.append(
                f"{status_icon:<10} {r.duration:>8.3f}s   {r.name:<50}"
            )
        
        # 统计
        lines.append("-" * 70)
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        total_time = sum(r.duration for r in results)
        
        lines.append(f"Total: {total} | Passed: {passed} | Failed: {failed} | Time: {total_time:.3f}s")
        
        return '\n'.join(lines)
    
    @staticmethod
    def to_csv(results: List[TestResult]) -> str:
        """转换为 CSV 格式
        
        用于数据分析
        
        Args:
            results: 测试结果列表
            
        Returns:
            CSV 字符串
        """
        if not results:
            return ""
        
        output = io.StringIO()
        fieldnames = ["name", "status", "duration", "message", "test_class", "timestamp"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for r in results:
            writer.writerow(asdict(r))
        
        return output.getvalue()
    
    @staticmethod
    def to_summary(results: List[TestResult]) -> Dict[str, Any]:
        """生成测试摘要
        
        用于快速了解测试状态
        
        Args:
            results: 测试结果列表
            
        Returns:
            摘要字典
        """
        if not results:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "success_rate": 0.0,
                "total_duration": 0.0
            }
        
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")
        total_time = sum(r.duration for r in results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "success_rate": (passed / total * 100) if total > 0 else 0.0,
            "total_duration": total_time,
            "avg_duration": total_time / total if total > 0 else 0.0
        }


def _xml_escape(text: str) -> str:
    """转义 XML 特殊字符"""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )


# 便捷函数
def format_json(results: List[TestResult], pretty: bool = False) -> str:
    """快捷函数：格式化为 JSON"""
    return TestResultFormatter.to_json(results, pretty)


def format_junit(results: List[TestResult], name: str = "UITestSuite") -> str:
    """快捷函数：格式化为 JUnit XML"""
    return TestResultFormatter.to_junit_xml(results, name)


def format_table(results: List[TestResult]) -> str:
    """快捷函数：格式化为表格"""
    return TestResultFormatter.to_table(results)


def format_summary(results: List[TestResult]) -> Dict[str, Any]:
    """快捷函数：生成摘要"""
    return TestResultFormatter.to_summary(results)
