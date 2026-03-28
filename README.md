# 教师数据中心 UI 自动化测试框架

> 基于 Playwright + Python + Pytest，支持完整的证据收集（视频/截图/Trace）+ 工具自进化 + 页面健康度监控

---

## 📊 项目概览

| 项目信息 | 详情 |
|---------|------|
| **测试系统** | 教师数据中心 |
| **系统 URL** | http://172.16.34.104:7777/dataapp/ |
| **测试框架** | Playwright + Python + Pytest |
| **Python 版本** | 3.12.12 (Conda 环境：manti) |
| **架构模式** | Page Object Model (POM) |
| **测试用例** | 46 个（35 P1, 8 P2, 3 废弃） |
| **特色功能** | 🔧 工具自进化 + 📊 页面健康度监控 |

---

## 🚀 快速开始

```bash
# 激活环境
conda activate manti
cd C:\11_UITest

# 运行所有测试
pytest tests/ -v

# 按模块运行
pytest tests/common/ -v           # 登录测试
pytest tests/teacher_data_center/ -v  # 我的数据测试

# 按优先级运行
pytest -m p1                    # 只跑 P1（冒烟）
pytest -m "p1 or p2"          # 跑 P1 + P2

# 打开报告
start reports\report.html
```

---

## 📁 项目结构

```
C:\11_UITest/
├── config/
│   └── config.yml              # 主配置（含LLM和进化配置）
├── pages/
│   ├── base_page.py           # 页面基类
│   ├── common/
│   │   └── login_page.py     # 登录页面
│   └── teacher_data_center/
│       └── my_data_page.py   # 我的数据页面
├── tests/
│   ├── conftest.py           # Pytest fixtures + 证据收集 + 健康度监控
│   ├── common/               # common 模块
│   │   ├── test_00_login.py
│   │   └── test_00_login_with_identity.py
│   └── teacher_data_center/  # teacher_data_center 模块
│       └── test_01_my_data.py
├── utils/
│   ├── browser_manager.py    # 浏览器管理
│   ├── logger.py            # 日志
│   ├── test_formatter.py   # 结果格式化
│   ├── page_explorer.py    # 页面探索工具 (AI 专用)
│   ├── cache_manager.py     # 分析结果缓存
│   ├── session_cache.py     # Session 登录缓存
│   ├── page_health_monitor.py  # ⭐ 页面健康度监控
│   ├── ocr_helper.py        # OCR 工具
│   ├── evolution/           # ⭐ 工具自进化框架
│   │   ├── registry.py      # 工具注册表
│   │   ├── decorator.py     # 进化装饰器
│   │   ├── enhancer.py      # 进化增强器
│   │   ├── llm_client.py    # LLM 客户端
│   │   └── scanner.py       # 目录扫描器
│   └── parsers/            # 解析器框架
│       ├── base_parser.py
│       └── playwright_parser.py
├── scripts/                  # 运维脚本
│   ├── check_naming_rules.py
│   └── evidence_cleaner.py
├── reports/
│   ├── report.html          # HTML 报告
│   ├── evidence/           # 证据（按模块分组）
│   │   ├── common/
│   │   └── teacher_data_center/
│   ├── page_analysis/     # 页面探索结果
│   │   ├── sessions/       # Session 缓存
│   │   └── common/        # 按模块存放
│   ├── evolution/         # ⭐ 工具进化记录
│   │   ├── 工具名称.json        # 工具执行记录
│   │   ├── 工具名称_report.md   # 进化报告
│   │   └── 工具名称_suggested.py # LLM建议代码
│   └── page_health/       # ⭐ 页面健康度报告
│       ├── health_report.md    # 总报告
│       └── 模块_页面.json       # 单页面记录
└── docs/                    # 详细文档
    ├── 页面分析规范.md
    ├── evolution_integration_guide.md      # ⭐ 进化机制集成指南
    └── health_monitor_integration_guide.md # ⭐ 健康度监控集成指南
```

---

## 🔑 核心特性

### 证据收集（自动）

| 证据类型 | PASS | FAIL |
|---------|------|------|
| 🎬 VIDEO | ✅ | ✅ |
| 📷 SCREENSHOT | - | ✅ |
| 🔍 TRACE | - | ✅ |
| 📄 PAGE | - | ✅ |

### HTML 报告
- 顶部分组摘要（模块 + 整体统计）
- 测试名称带模块前缀
- 证据列直接可点击
- 源码列链接到测试文件

### 测试标记
```python
@pytest.mark.p1   # 核心功能
@pytest.mark.p2   # 重要功能
@pytest.mark.p3   # 一般功能
```

### 页面探索工具 (Page Explorer)

AI 专用工具，用于自动分析页面并生成 Page Object。

```python
from utils.page_explorer import PageExplorer

explorer = PageExplorer()

# 登录并缓存 Session
explorer.login(
    url="http://172.16.34.104:7777/dataapp/login",
    username="T100002",
    password="wisedu@1",
    verify_code="2222",
    identity="信息中心管理员"
)

# 探索页面
result = explorer.explore(url="...", module="common", page_name="login")

# 生成 POM 代码
pom_code = explorer.generate_pom(result["snapshot"], module="common", page_name="login")
```

探索结果保存在 `reports/page_analysis/` 目录。

### Selector 版本管理与 Fallback

当页面元素变化时，Fallback 机制确保测试不挂。

```python
class LoginPage(BasePage):
    SELECTORS_VERSION = "v20260327"
    SELECTORS_HISTORY = {
        "v1": { "USERNAME": "input[placeholder*='用户名']" },
        "v20260327": { "USERNAME": "input[placeholder*='请输入用户名']" },
    }
```

BasePage 会自动回退到历史 selector，测试用例无需修改。

---

## 🔧 工具自进化机制

基于 Yunjue-Agent 的 In-situ Self-Evolving (ISE) 范式，实现框架工具类的智能改进。

### 核心特性

- **自动监控**: 装饰器自动记录工具执行结果
- **智能分析**: LLM 分析失败原因（参数错误/代码bug/环境问题）
- **代码生成**: 自动生成改进代码
- **安全可控**: 默认需人工审核后才应用

### 工作流程

```
工具执行 → 装饰器记录 → 失败累积 ≥3次 → LLM分析 → 生成改进代码 → 人工审核 → 应用改进
```

### 已监控工具

```
scripts/
└── page_analyzer.quick_evaluate

utils/
├── page_explorer.login/explore/generate_pom
├── session_cache.save/load
└── ocr_helper.recognize_text
```

### 配置 (config.yml)

```yaml
llm:
  api_base: http://localhost:11434/v1  # Ollama/LocalAI
  model: qwen2.5:14b

evolution:
  enabled: true
  failure_threshold: 3        # 连续失败3次触发进化
  auto_apply: false           # 需人工审核
```

### 查看进化报告

```bash
# 查看工具进化报告
ls reports/evolution/*_report.md

# 查看LLM建议的改进代码
cat reports/evolution/工具名称_suggested.py
```

---

## 📊 页面健康度监控

自动监控页面测试成功率，识别需要修改/合并/重构的页面。

### 监控指标

| 指标 | 说明 | 阈值 |
|------|------|------|
| **健康度** | 综合评分 (0-100) | < 50 紧急修复 |
| **成功率** | 测试通过率 | < 30% 页面可能下线 |
| **Selector变更** | 定位策略稳定性 | ≥ 3 次需重构 |
| **探索失败** | 页面结构变化 | ≥ 3 次需重新探索 |

### 自动生成报告

```bash
# 运行测试后自动生成
pytest tests/ -v

# 查看健康度报告
cat reports/page_health/health_report.md
```

### 报告示例

```
## 🚨 需要关注的页面

| 模块 | 页面 | 健康度 | 成功率 | 状态 |
|------|------|--------|--------|------|
| teacher | my_data | 🔴 55.0 | 25.0% | critical |

## 🔀 建议合并的页面

| 模块 | 页面 | 重复页面列表 |
|------|------|--------------|
| teacher | my_data | teacher/data_view |
```

### 集成到工作流

```python
# tests/conftest.py

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试结果钩子 - 自动记录页面健康度"""
    outcome = yield
    report = outcome.get_result()
    
    if call.when == "call":
        monitor = get_page_health_monitor()
        monitor.record_test(
            module=test_module,
            page_name=page_name,
            url=url,
            success=report.passed
        )
```

### 核心价值

- 📊 **数据驱动决策**: 不再凭感觉维护测试
- 🔄 **自动化闭环**: 与工具自进化联动
- 📈 **持续优化**: 测试框架越用越稳定

---

## 🧪 测试状态

| 模块 | 用例 | 状态 |
|------|------|------|
| common（登录） | 2 | ✅ 通过 |
| teacher_data_center（我的数据） | 2 | ⏳ 待修复 |

---

## 📖 文档导航

| 文档 | 说明 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 5 分钟快速上手 |
| [tests/README.md](tests/README.md) | 如何编写测试用例 |
| [reports/README.md](reports/README.md) | 如何查看报告和证据 |
| [docs/页面分析规范.md](docs/页面分析规范.md) | 页面分析 SOP |
| [docs/evolution_integration_guide.md](docs/evolution_integration_guide.md) | ⭐ 工具自进化集成指南 |
| [docs/health_monitor_integration_guide.md](docs/health_monitor_integration_guide.md) | ⭐ 页面健康度监控集成指南 |
| [config/config.yml](config/config.yml) | 配置文件说明 |
| [AGENTS.md](AGENTS.md) | AI Agent 完整文档 |

---

## 🛠️ 常用命令

```bash
# ========== 测试执行 ==========
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/common/test_00_login.py::TestLogin::test_login_success -v

# 慢速调试（显示浏览器）
pytest --headed --slowmo=1000

# 只跑失败的测试
pytest --lf

# ========== 证据查看 ==========
# 查看 Trace（最详细证据）
playwright show-trace evidence/common/test_login_success/trace.zip

# 打开 HTML 报告
start reports\report.html

# ========== 工具自进化 ==========
# 查看进化报告
ls reports/evolution/*_report.md

# 查看LLM建议的改进代码
cat reports/evolution/page_explorer.login_suggested.py

# 运行进化机制测试
python test_evolution_simple.py

# ========== 页面健康度 ==========
# 查看健康度报告
cat reports/page_health/health_report.md

# 查看特定页面记录
cat reports/page_health/common_login.json

# ========== 运维脚本 ==========
# 检查命名规范
python scripts/check_naming_rules.py

# 清理旧证据
python scripts/evidence_cleaner.py
```

---

## 🔄 日常维护指南

### 每日检查

```bash
# 1. 运行测试
pytest tests/ -v

# 2. 检查失败用例
# 查看 HTML 报告中的失败用例

# 3. 查看工具进化报告
ls reports/evolution/*_report.md

# 4. 查看页面健康度
cat reports/page_health/health_report.md
```

### 每周优化

```bash
# 1. 检查健康度报告，识别问题页面
cat reports/page_health/health_report.md

# 2. 修复高失败率页面（健康度 < 50）
pytest tests/模块/test_页面.py -v --headed

# 3. 审核进化报告，决定是否采纳改进
cat reports/evolution/工具名称_suggested.py

# 4. 合并重复页面（建议合并的页面）
# 手动合并 POM 类

# 5. 重构不稳定 selector（变更次数 ≥ 3）
# 使用 data-* 属性
```

### 有问题？查看 reports/README.md 或 tests/README.md** 🦐

---

## 🎯 演示脚本

```bash
# 工具自进化机制演示
python demo_evolution_workflow.py

# 页面健康度监控演示
python demo_page_health_monitor.py

# 完整集成演示
python demo_health_integration.py

# AI 工作流演示（带进化）
python demo_ai_workflow_with_evolution.py
```

---

**项目维护：定期查看健康度报告，基于数据驱动优化测试框架** 🚀
