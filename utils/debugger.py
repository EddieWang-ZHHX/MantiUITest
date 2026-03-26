"""
结构化 Debug 工具 - 基于 Superpowers systematic-debugging

4 步 debug 流程：
1. 收集证据 (Collect Evidence)
2. 建立假设 (Form Hypotheses)
3. 逐个排除 (Eliminate)
4. 验证修复 (Verify Fix)

使用方式:
    from utils.debugger import StructuredDebugger
    debugger = StructuredDebugger(test_name, evidence_dir)
    debugger.collect()           # 自动收集所有证据
    debugger.report()            # 生成 debug 报告
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class DebugFinding:
    """Debug 发现"""
    type: str           # "screenshot" | "trace" | "log" | "html" | "console"
    path: str
    timestamp: str
    description: str
    key_info: Dict = field(default_factory=dict)


@dataclass
class DebugHypothesis:
    """Debug 假设"""
    id: int
    description: str
    probability: str    # "高" | "中" | "低"
    evidence: List[str] = field(default_factory=list)
    ruled_out: bool = False
    elimination_method: str = ""


class StructuredDebugger:
    """
    结构化 Debug 工具
    
    4 步流程：
    Step 1: 收集证据 - 自动收集 screenshot / trace / log / html / console
    Step 2: 建立假设 - 根据证据列出可能原因
    Step 3: 逐个排除 - 用最小改动验证每个假设
    Step 4: 验证修复 - 重新运行测试确认问题解决
    """
    
    # 常见失败原因字典（用于自动建议假设）
    COMMON_FAILURES = {
        "login": [
            ("定位器失效", "高", ["截图显示元素不存在", "控制台无错误"]),
            ("验证码错误", "中", ["测试固定验证码", "验证码已过期"]),
            ("网络超时", "中", ["日志显示超时", "偶发性"]),
            ("身份选择失败", "低", ["截图显示身份弹窗", "多身份账号"]),
        ],
        "navigation": [
            ("URL 不匹配", "高", ["日志显示预期 URL", "实际 URL 不同"]),
            ("页面加载超时", "高", ["trace 显示 pending 请求", "网络慢"]),
            ("元素未渲染", "中", ["截图显示空白或 Loading", "需要等待"]),
        ],
        "assertion": [
            ("预期结果错误", "高", ["测试用例设计问题", "需求变更"]),
            ("数据不一致", "中", ["测试数据被污染", "数据库状态不对"]),
            ("时序问题", "中", ["截图显示正确但断言失败", "需要显式等待"]),
        ],
        "default": [
            ("定位器失效", "高", ["截图显示元素不存在"]),
            ("页面结构变化", "中", ["截图显示布局改变", "前端升级了"]),
            ("网络请求失败", "中", ["控制台有 4xx/5xx 错误"]),
            ("测试数据问题", "低", ["测试数据不存在或被占用"]),
        ]
    }
    
    def __init__(self, test_name: str, evidence_dir: str = None):
        self.test_name = test_name
        self.project_root = Path(__file__).parent.parent
        self.evidence_dir = Path(evidence_dir) if evidence_dir else self.project_root / "reports" / "evidence" / test_name
        self.findings: List[DebugFinding] = []
        self.hypotheses: List[DebugHypothesis] = []
        self.failure_category = "default"
        self.failure_error = ""
        self.failure_screenshot = ""
        self.failure_log = ""
        
        # 初始化时间戳
        self.debug_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ========== Step 1: 收集证据 ==========
    
    def collect(self) -> "StructuredDebugger":
        """
        Step 1: 收集证据
        
        自动扫描 evidence_dir，收集所有可用证据文件
        """
        print("\n" + "=" * 60)
        print(f"🔍 [Step 1/4] 收集证据: {self.test_name}")
        print("=" * 60)
        
        if not self.evidence_dir.exists():
            print(f"❌ 证据目录不存在: {self.evidence_dir}")
            return self
        
        evidence_files = {
            "screenshot": [],
            "trace": [],
            "log": [],
            "html": [],
            "console": [],
            "video": []
        }
        
        for f in self.evidence_dir.iterdir():
            if f.is_file():
                name_lower = f.name.lower()
                if "screenshot" in name_lower:
                    evidence_files["screenshot"].append(f)
                elif "trace" in name_lower and f.suffix == ".zip":
                    evidence_files["trace"].append(f)
                elif "page" in name_lower and f.suffix == ".html":
                    evidence_files["html"].append(f)
                elif f.name == "console.log":
                    evidence_files["console"].append(f)
                elif "video" in name_lower and f.suffix == ".webm":
                    evidence_files["video"].append(f)
        
        # 失败相关的证据（优先）
        for f in evidence_files["screenshot"]:
            if "failed" in f.name.lower() or len(evidence_files["screenshot"]) == 1:
                self.findings.append(DebugFinding(
                    type="screenshot",
                    path=str(f),
                    timestamp=self._get_file_time(f),
                    description="失败截图",
                    key_info={"is_failure_screenshot": "failed" in f.name.lower()}
                ))
                self.failure_screenshot = str(f)
                break
        
        for f in evidence_files["trace"]:
            self.findings.append(DebugFinding(
                type="trace",
                path=str(f),
                timestamp=self._get_file_time(f),
                description="Playwright Trace（包含完整 DOM 快照）",
                key_info={"size_kb": f.stat().st_size // 1024}
            ))
        
        for f in evidence_files["html"]:
            self.findings.append(DebugFinding(
                type="html",
                path=str(f),
                timestamp=self._get_file_time(f),
                description="失败时页面 HTML"
            ))
            self.failure_log = str(f)
        
        for f in evidence_files["console"]:
            self.findings.append(DebugFinding(
                type="console",
                path=str(f),
                timestamp=self._get_file_time(f),
                description="浏览器控制台日志",
                key_info=self._parse_console_log(f)
            ))
        
        # 打印证据清单
        print(f"\n📁 证据目录: {self.evidence_dir}")
        print(f"📊 找到 {len(self.findings)} 个证据文件:\n")
        
        for finding in self.findings:
            icon = {"screenshot": "📷", "trace": "🔍", "html": "📄", "console": "📝"}.get(finding.type, "📎")
            print(f"  {icon} [{finding.type.upper()}] {Path(finding.path).name}")
            print(f"     {finding.description}")
            if finding.key_info:
                for k, v in finding.key_info.items():
                    print(f"     - {k}: {v}")
            print()
        
        return self
    
    # ========== Step 2: 建立假设 ==========
    
    def suggest_hypotheses(self, failure_category: str = "default", custom_error: str = "") -> "StructuredDebugger":
        """
        Step 2: 建立假设
        
        根据证据和失败类型，列出可能的假设
        """
        print("\n" + "=" * 60)
        print(f"💡 [Step 2/4] 建立假设 (Failure Category: {failure_category})")
        print("=" * 60)
        
        self.failure_category = failure_category
        self.failure_error = custom_error
        
        # 获取该类别的常见假设
        category_failures = self.COMMON_FAILURES.get(
            failure_category, 
            self.COMMON_FAILURES["default"]
        )
        
        for i, (desc, prob, evidence) in enumerate(category_failures, 1):
            hypothesis = DebugHypothesis(
                id=i,
                description=desc,
                probability=prob,
                evidence=evidence
            )
            self.hypotheses.append(hypothesis)
        
        print(f"\n🔎 基于 '{failure_category}' 类型，列出 {len(self.hypotheses)} 个可能原因:\n")
        
        for h in self.hypotheses:
            prob_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(h.probability, "⚪")
            status = "⏳ 待验证" if not h.ruled_out else "❌ 已排除"
            print(f"  [{h.id}] {prob_icon} {h.description} (概率: {h.probability}) {status}")
            if h.evidence:
                print(f"       依据: {'; '.join(h.evidence)}")
        
        return self
    
    # ========== Step 3: 逐个排除 ==========
    
    def eliminate(self, hypothesis_id: int, reason: str) -> "StructuredDebugger":
        """
        Step 3: 排除假设
        
        标记某个假设为已排除，并说明原因
        """
        for h in self.hypotheses:
            if h.id == hypothesis_id:
                h.ruled_out = True
                h.elimination_method = reason
                print(f"\n❌ 排除假设 [{h.id}] {h.description}")
                print(f"   原因: {reason}")
                break
        
        return self
    
    def get_remaining_hypotheses(self) -> List[DebugHypothesis]:
        """获取还未排除的假设"""
        return [h for h in self.hypotheses if not h.ruled_out]
    
    # ========== Step 4: 验证修复 ==========
    
    def verify(self, test_command: str = None) -> bool:
        """
        Step 4: 验证修复
        
        询问用户是否验证了修复
        """
        print("\n" + "=" * 60)
        print(f"✅ [Step 4/4] 验证修复")
        print("=" * 60)
        
        remaining = self.get_remaining_hypotheses()
        if remaining:
            print(f"\n⚠️  还有 {len(remaining)} 个假设未排除，问题可能未完全解决:")
            for h in remaining:
                print(f"  - [{h.id}] {h.description} (概率: {h.probability})")
        
        print(f"\n请执行以下验证:")
        if test_command:
            print(f"  1. 运行: {test_command}")
        print(f"  2. 确认测试通过")
        print(f"  3. 如果通过，说明问题已修复")
        print(f"  4. 如果仍失败，回到 Step 1 重新收集证据")
        
        return len(remaining) == 0
    
    # ========== 生成报告 ==========
    
    def report(self) -> str:
        """生成完整的 debug 报告"""
        lines = [
            "",
            "=" * 60,
            f"🐛 DEBUG REPORT: {self.test_name}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "【Step 1: 证据收集】",
            f"证据目录: {self.evidence_dir}",
            f"找到 {len(self.findings)} 个证据:",
        ]
        
        for f in self.findings:
            lines.append(f"  - [{f.type.upper()}] {Path(f.path).name}")
            lines.append(f"    {f.description}")
        
        lines.extend([
            "",
            "【Step 2: 假设分析】",
            f"失败类型: {self.failure_category}",
        ])
        
        if self.failure_error:
            lines.append(f"错误信息: {self.failure_error}")
        
        lines.append(f"共 {len(self.hypotheses)} 个假设:")
        for h in self.hypotheses:
            status = "❌ 已排除" if h.ruled_out else "⏳ 待验证"
            lines.append(f"  [{h.id}] {h.description} (概率: {h.probability}) {status}")
            if h.ruled_out:
                lines.append(f"       排除方法: {h.elimination_method}")
        
        remaining = self.get_remaining_hypotheses()
        if remaining:
            lines.extend(["", "⚠️  未解决的假设:"])
            for h in remaining:
                lines.append(f"  - [{h.id}] {h.description}")
        
        lines.extend(["", "=" * 60])
        
        report = "\n".join(lines)
        print(report)
        return report
    
    def save_report(self, output_path: str = None) -> str:
        """保存报告到文件"""
        if output_path is None:
            output_path = str(self.evidence_dir / "debug_report.txt")
        
        report = self.report()
        Path(output_path).write_text(report, encoding="utf-8")
        print(f"\n💾 报告已保存: {output_path}")
        return output_path
    
    # ========== 辅助方法 ==========
    
    def _get_file_time(self, f: Path) -> str:
        try:
            ts = f.stat().st_mtime
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "未知"
    
    def _parse_console_log(self, f: Path) -> Dict:
        """解析控制台日志，提取错误"""
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            errors = []
            lines = content.split("\n")
            for line in lines:
                if any(kw in line.lower() for kw in ["error", "exception", "failed", "uncaught"]):
                    errors.append(line.strip()[:100])
            return {"error_count": len(errors), "sample_errors": errors[:5]}
        except:
            return {"error_count": 0}
    
    # ========== 快速使用入口 ==========
    
    @staticmethod
    def quick_debug(test_name: str, failure_category: str = "default", 
                   custom_error: str = "") -> "StructuredDebugger":
        """
        快速 debug 入口
        
        用法:
            debugger = StructuredDebugger.quick_debug(
                "test_login_success",
                failure_category="login",
                custom_error="元素不可点击"
            )
            debugger.report()
        """
        return StructuredDebugger(test_name).collect().suggest_hypotheses(
            failure_category=failure_category,
            custom_error=custom_error
        )


if __name__ == "__main__":
    # 演示用法
    print("结构化 Debug 工具演示\n")
    
    # 模拟一个 login 测试的 debug
    debugger = StructuredDebugger("test_login_success")
    debugger.collect()
    debugger.suggest_hypotheses("login")
    debugger.report()
