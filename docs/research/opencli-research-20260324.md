# OpenCLI 研究报告

**研究日期**: 2026-03-24
**项目**: jackwener/opencli
** Stars**: 5636 | **Forks**: 458 | **语言**: TypeScript

---

## 📋 项目概述

OpenCLI 是一个通用的 CLI Hub，能够将**任何网站、Electron 应用或本地工具**转化为命令行接口。它专门为 AI Agent 设计，支持浏览器会话复用、AI 驱动的 API 发现和自动适配器生成。

**核心理念**: "Make Any Website & Tool Your CLI"

---

## 🏗️ 架构分析

### Dual-Engine Architecture

```
┌─────────────────────────────────────────────────────┐
│ opencli CLI (Commander.js entry point)              │
├─────────────────────────────────────────────────────┤
│ Engine Layer                                        │
│ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │
│ │ Registry     │ │ Dynamic      │ │ Output      │ │
│ │ (commands)   │ │ Loader       │ │ Formatter   │ │
│ └──────────────┘ └──────────────┘ └────────────┘ │
├─────────────────────────────────────────────────────┤
│ Adapter Layer                                       │
│ ┌─────────────────┐ ┌──────────────────────────┐  │
│ │ YAML Pipeline   │ │ TypeScript Adapters      │  │
│ │ (declarative)  │ │ (browser/desktop/AI)     │  │
│ └─────────────────┘ └──────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│ Connection Layer                                    │
│ ┌─────────────────┐ ┌──────────────────────────┐  │
│ │ Browser Bridge  │ │ CDP (Chrome DevTools)    │  │
│ │ (Extension+WS)  │ │ (Electron apps)         │  │
│ └─────────────────┘ └──────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 认证策略 (5-Tier)

| Tier | 策略 | 速度 | 适用场景 |
|------|------|------|----------|
| 1 | public | ⚡ ~1s | 公开 API，无需登录 |
| 2 | cookie | 🔄 ~7s | Cookie 认证即可 |
| 3 | header | 🔄 ~7s | 需要 CSRF/Bearer token |
| 4 | intercept | 🔄 ~10s | 复杂签名，XHR 拦截 |
| 5 | ui | 🐌 ~15s+ | 无 API，纯 DOM 解析 |

---

## 🎯 对 UI 自动化框架的参考价值

### 1. ✅ 可以借鉴的理念

#### 1.1 动态加载器 (Dynamic Loader)

**OpenCLI**: 只需把 `.yaml` 或 `.ts` 文件放入 `clis/` 目录，自动注册。

**当前框架问题**: 所有页面对象需要在 `conftest.py` 或测试文件中手动导入。

**借鉴方案**:
```python
# pages/__init__.py 或动态导入
import os
import importlib
from pathlib import Path

def discover_pages():
    """自动发现 pages/ 目录下的所有页面对象"""
    pages_dir = Path(__file__).parent
    for py_file in pages_dir.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue
        module_name = f"pages.{py_file.stem}"
        module = importlib.import_module(module_name)
        # 自动注册到页面池
```

#### 1.2 输出格式化 (Output Formatter)

**OpenCLI**: 统一输出格式 (table, json, yaml, md, csv)

**当前框架问题**: 测试报告是 HTML，但测试结果数据结构不一致。

**借鉴方案**:
```python
# utils/output_formatter.py
class OutputFormatter:
    FORMATS = ["table", "json", "yaml", "md", "csv"]
    
    def format(self, data: list, format: str = "table") -> str:
        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format == "table":
            return self._to_table(data)
        # ...
```

#### 1.3 认证策略框架

**OpenCLI**: 5-Tier 认证策略自动探测

**当前框架问题**: 登录处理是硬编码的，没有统一的认证策略。

**借鉴方案**:
```python
# utils/auth_strategy.py
class AuthStrategy:
    TIERS = ["public", "cookie", "header", "intercept", "ui"]
    
    @staticmethod
    def detect(responses) -> str:
        """自动检测认证策略"""
        for tier in AuthStrategy.TIERS:
            if AuthStrategy._matches_tier(responses, tier):
                return tier
        return "ui"
```

#### 1.4 AI-Agent 工作流

**OpenCLI**: `explore` → `synthesize` → `generate` → `cascade`

**当前框架问题**: 页面分析是手动的，没有自动化流程。

**借鉴方案**:
```python
# utils/page_discover.py
class PageDiscover:
    def explore(self, url: str) -> dict:
        """发现页面 API 端点和元素"""
        # 1. 导航到页面
        # 2. 抓取网络请求
        # 3. 分析 DOM 结构
        # 4. 输出 manifest.json
        
    def generate_page_object(self, manifest: dict) -> str:
        """从发现结果生成页面对象代码"""
        # 读取模板，填充占位符
```

### 2. ⚠️ 需要谨慎借鉴的

#### 2.1 YAML 声明式 Pipeline

**OpenCLI**: `navigate` + `evaluate` + `map` + `limit`

**评估**: 对于简单操作很优雅，但复杂测试场景（多步骤、条件分支、数据验证）不适合用 YAML 表达。

**结论**: 保持 Python/Pytest 框架，YAML 仅用于配置而非测试逻辑。

#### 2.2 浏览器会话复用

**OpenCLI**: 通过 Chrome Extension 复用已登录状态

**评估**: 对需要登录的网站很有价值，但当前框架每次测试都是全新 session。

**结论**: 可以考虑增加 `reuse_session` 选项，但需要解决测试隔离问题。

### 3. ❌ 不适用的理念

#### 3.1 CLI 命令模式

**OpenCLI**: 面向命令，数据提取为主

**当前框架**: 面向测试，验证为主

**结论**: 核心目标不同，不适合照搬。

#### 3.2 拦截器模式

**OpenCLI**: 拦截网络请求获取数据

**当前框架**: 验证 UI 元素状态和行为

**结论**: 可用于 API 测试，但不适合 UI 测试。

---

## 📊 具体改进建议

### 优先级 高

#### 1. 页面对象自动发现

**文件**: `pages/__init__.py`

```python
"""页面对象自动发现系统"""
from pathlib import Path
from typing import Dict, Type
from pages.base_page import BasePage

# 全局页面池
PAGE_POOL: Dict[str, Type[BasePage]] = {}

def register_page(name: str, page_class: Type[BasePage]):
    """注册页面对象"""
    PAGE_POOL[name] = page_class

def get_page(name: str) -> Type[BasePage]:
    """获取页面对象"""
    if name not in PAGE_POOL:
        raise ValueError(f"Unknown page: {name}. Available: {list(PAGE_POOL.keys())}")
    return PAGE_POOL[name]

def discover_pages():
    """自动发现并注册所有页面对象"""
    pages_dir = Path(__file__).parent
    for py_file in pages_dir.rglob("*_page.py"):
        if py_file.name.startswith("_"):
            continue
        module_name = f"pages.{py_file.stem}"
        module = __import__(module_name, fromlist=[""])
        
        # 查找页面类 (命名规则: XxxPage)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) 
                and issubclass(attr, BasePage)
                and attr is not BasePage
                and attr_name.endswith("Page")):
                page_name = attr_name[:-4].lower()  # "LoginPage" -> "login"
                register_page(page_name, attr)

# 启动时自动发现
discover_pages()
```

#### 2. 测试结果统一输出

**文件**: `utils/test_formatter.py`

```python
"""测试结果格式化"""
import json
from typing import List, Dict, Any

class TestResultFormatter:
    """统一格式化测试结果"""
    
    @staticmethod
    def to_json(results: List[Dict[str, Any]]) -> str:
        return json.dumps(results, indent=2, ensure_ascii=False)
    
    @staticmethod
    def to_table(results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No results"
        
        headers = list(results[0].keys())
        lines = []
        lines.append(" | ".join(headers))
        lines.append("-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1)))
        
        for row in results:
            values = [str(row.get(h, "")) for h in headers]
            lines.append(" | ".join(values))
        
        return "\n".join(lines)
    
    @staticmethod
    def to_csv(results: List[Dict[str, Any]]) -> str:
        if not results:
            return ""
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        
        return output.getvalue()
```

#### 3. 页面分析工具增强

**文件**: `utils/page_analyzer.py` (已有，增强)

```python
"""页面分析工具 - OpenCLI 的 explore 理念"""

class PageExplorer:
    """探索页面结构，生成页面对象"""
    
    def __init__(self, page):
        self.page = page
    
    def analyze(self, url: str) -> dict:
        """分析页面结构"""
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        
        return {
            "title": self.page.title(),
            "url": url,
            "forms": self._find_forms(),
            "buttons": self._find_buttons(),
            "inputs": self._find_inputs(),
            "links": self._find_links(),
            "api_endpoints": self._capture_api_endpoints(),
        }
    
    def _find_forms(self) -> List[dict]:
        """查找所有表单"""
        forms = self.page.query_selector_all("form")
        return [{
            "action": form.get_attribute("action"),
            "method": form.get_attribute("method"),
            "inputs": form.query_selector_all("input")
        } for form in forms]
    
    def _find_buttons(self) -> List[str]:
        """查找所有按钮文本"""
        return [btn.inner_text() for btn in self.page.query_selector_all("button")]
    
    def generate_page_object_code(self, analysis: dict) -> str:
        """从分析结果生成页面对象代码"""
        template = '''
class {name}Page(BasePage):
    """自动生成的页面对象"""
    
    # 元素定位器
{locators}
    
    def __init__(self, page, base_url=""):
        super().__init__(page, base_url)
    
    def navigate_to(self):
        return self.open("{url}")
'''
        # 生成代码...
        return template
```

### 优先级 中

#### 4. 认证策略检测

**文件**: `utils/auth_detector.py`

```python
"""认证策略检测 - 借鉴 OpenCLI 5-Tier"""

from enum import Enum
from typing import Optional

class AuthTier(Enum):
    PUBLIC = "public"      # 无需认证
    COOKIE = "cookie"     # Cookie 认证
    HEADER = "header"      # Header 认证
    INTERCEPT = "intercept" # 请求拦截
    UI = "ui"             # UI 自动化

class AuthDetector:
    """检测网站认证策略"""
    
    @staticmethod
    def detect(page) -> AuthTier:
        """
        自动检测认证策略
        
        1. 尝试直接 API 调用 (public)
        2. 尝试带 Cookie 的 API 调用 (cookie)
        3. 尝试带 Header 的 API 调用 (header)
        4. 尝试请求拦截 (intercept)
        5. 回退到 UI 自动化 (ui)
        """
        # 实现检测逻辑...
        pass
```

#### 5. 证据收集增强

**文件**: `utils/evidence_collector.py`

```python
"""证据收集系统 - 增强版"""

class EvidenceCollector:
    """收集测试证据，支持多种格式"""
    
    FORMATS = ["html", "json", "yaml", "csv"]
    
    def __init__(self, test_name: str, output_dir: str):
        self.test_name = test_name
        self.output_dir = Path(output_dir)
    
    def collect(self, page, error: Optional[str] = None):
        """收集所有证据"""
        self._save_screenshot(page)
        self._save_html(page)
        self._save_trace()
        self._save_console_logs(page)
        
        if error:
            self._save_error_report(error)
    
    def export(self, format: str = "json") -> str:
        """导出测试报告"""
        if format == "json":
            return self._to_json()
        elif format == "yaml":
            return self._to_yaml()
        # ...
```

---

## 🔄 与当前框架的对比

| 维度 | OpenCLI | 当前框架 | 差距 |
|------|---------|----------|------|
| **目标** | CLI 命令生成 | UI 测试验证 | 不同但互补 |
| **语言** | TypeScript | Python | 不同 |
| **认证** | 5-Tier 自动检测 | 硬编码 | 需要改进 |
| **动态加载** | 是 | 否 | 需要改进 |
| **输出格式** | 多格式 | 仅 HTML | 需要改进 |
| **页面发现** | explore | 手动 | 需要改进 |
| **测试隔离** | N/A | 是 | 已有 |
| **证据收集** | 基础 | 完整 | 当前更好 |

---

## 📈 实施路线图

### Phase 1: 快速改进 (1-2 天)

1. **页面对象自动发现** - 减少手动导入
2. **测试结果格式化** - 统一输出格式
3. **更新文档** - 记录新功能

### Phase 2: 中期改进 (1 周)

1. **认证策略框架** - 统一登录处理
2. **页面分析工具** - 自动生成定位器
3. **YAML 配置增强** - 支持更复杂的测试场景

### Phase 3: 长期改进 (2-4 周)

1. **AI 辅助测试生成** - 从页面分析自动生成测试
2. **跨平台支持** - Firefox, WebKit
3. **并行执行优化** - 加速测试套件

---

## ✅ 结论

**参考价值**: ⭐⭐⭐⭐ (4/5)

**核心借鉴点**:
1. 动态加载机制 - 提升框架可扩展性
2. 输出格式化 - 提升报告可用性
3. 认证策略框架 - 统一登录处理
4. 页面探索理念 - 向自动化分析迈进

**不适用的部分**:
- CLI 命令模式
- 拦截器数据提取
- YAML 测试逻辑

**最终建议**: 
将 OpenCLI 的 **架构理念** (动态加载、输出格式化、认证分层) 融入当前框架，但保持 **测试验证** 的核心定位，不盲目追求命令式交互。
