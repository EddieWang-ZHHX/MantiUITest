# 教师数据中心 UI 自动化测试框架

> **专业的、可审计的 UI 自动化测试框架**
> 基于 Playwright + Python + Pytest，支持完整的证据收集（视频/截图/Trace）

---

## 📊 项目概览

| 项目信息 | 详情 |
|---------|------|
| **测试系统** | 教师数据中心 (Teacher Data Center) |
| **系统 URL** | http://172.16.34.104:7777/dataapp |
| **测试框架** | Playwright + Python + Pytest |
| **Python 版本** | 3.12.12 (Conda 环境：manti) |
| **架构模式** | Page Object Model (POM) |
| **证据收集** | 视频录制 + 截图 + Playwright Trace + 详细日志 |
| **测试用例来源** | `docs/analysis_test_cases_md/` |

---

## 🏗️ 核心架构

### Session 级登录复用

整个测试 session 只启动**一次浏览器、执行一次登录**，所有测试共享同一个 Page 实例：

```
session 级 fixtures:
  browser_manager    ← 单浏览器实例，session 全局复用
  page              ← 单 Page 实例，所有测试共享
  logged_in_admin   ← 信息中心管理员身份，只登录 1 次
  logged_in_teacher ← 教师身份，只登录 1 次
```

**节省时间**：每个测试平均节省 5-10 秒登录开销，11 个用例约节省 55-110 秒。

### 并发支持

每个测试自主 navigate 到目标页面，**不依赖其他测试留下的页面状态**，天然支持 pytest-xdist 并行：

```bash
# 并行执行（-n auto 根据 CPU 核心数自动分配）
pytest tests -n auto -v
```

### 测试设计原则

1. **身份分组**：`logged_in_admin` 覆盖 90% 场景（申请+审批自己完成），`logged_in_teacher` 仅用于必须教师身份的场景
2. **页面自主导航**：每个测试内部调用 `navigate_to()`，不假设页面状态
3. **真正的多身份场景**：才拆分独立模块（如 T100004 申请、T100002 审核）

---

## 📁 目录结构

```
C:\11_UITest\
├── config/
│   └── config.yaml              # 主配置（URL、账号、证据收集策略）
├── pages/                       # Page Object Model
│   ├── base_page.py            # 基类
│   ├── common/
│   │   └── login_page.py       # 登录页
│   └── teacher_data_center/
│       ├── my_data_page.py     # 我的数据页面
│       └── teacher_data_query_page.py  # 教师数据查询
├── tests/
│   ├── conftest.py             # Pytest fixtures（session 级）
│   ├── common/
│   │   └── test_login.py       # 登录测试
│   └── teacher_data_center/
│       ├── test_my_data.py          # 我的数据
│       ├── test_my_data_table.py    # 家庭成员表格 CRUD
│       ├── test_my_data_form.py     # 博士后表单 CRUD
│       └── test_teacher_data_query.py  # 教师数据查询
├── utils/
│   └── _core/
│       └── browser_manager.py   # 浏览器生命周期管理
├── reports/
│   ├── report.html             # HTML 报告
│   └── evidence/               # 证据目录
└── docs/
    └── analysis_test_cases_md/  # 测试场景文档
```

---

## 🚀 快速开始

### 启动 Chrome 调试模式

```bash
# 双击桌面 Chrome-Debug.bat，或命令行启动
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

### 运行测试

```bash
# 顺序执行（session 级复用生效，登录只执行 1 次）
cd C:\11_UITest
C:\Users\Eddie\miniconda3\envs\manti\python.exe -m pytest tests -v

# 并行执行（不同 worker 进程各自独立登录）
C:\Users\Eddie\miniconda3\envs\manti\python.exe -m pytest tests -n auto -v
```

### 查看报告

```bash
# HTML 报告（包含视频/截图/Trace 链接）
start C:\11_UITest\reports\report.html

# 证据目录
C:\11_UITest\reports\evidence\
```

---

## 🎯 Fixtures 说明

| Fixture | Scope | 身份 | 适用场景 |
|--------|-------|------|---------|
| `logged_in_admin` | session | 信息中心管理员 | 90% 场景：申请、审批、查询 |
| `logged_in_teacher` | session | 教师 | 必需教师身份的场景 |
| `create_page(name)` | session | - | 动态创建任意页面对象 |

### 使用示例

```python
# 场景 1：管理员通吃（申请+审批同身份）
def test_audit_self_approval(logged_in_admin):
    page = logged_in_admin.page
    my_data = MyDataPage(page, base_url)
    my_data.navigate_to()
    # ... 申请
    # ... 自己审批

# 场景 2：教师身份（必需时）
def test_teacher_basic_info(logged_in_teacher):
    page = logged_in_teacher.page
    my_data = MyDataPage(page, base_url)
    my_data.navigate_to()
    # ...

# 场景 3：动态创建页面对象
def test_data_query(logged_in_admin, create_page):
    query = create_page("teacher_data_query")
    query.navigate_to()
```

---

## 🔧 配置说明

### 配置文件

`config/config.yaml` 是唯一主配置：

```yaml
# 测试系统
test:
  base_url: http://172.16.34.104:7777/dataapp

# 认证（默认测试账号）
auth:
  default_username: T100002
  default_password: wisedu@1
  default_verify_code: "2222"
  default_group: 信息中心管理员

# 证据收集（always=始终录制，on_failure=失败时录制）
evidence:
  video: always
  screenshot: always
  page_html: always
  trace: always
```

---

## 🧪 测试用例状态

### 已实现测试

| 测试文件 | 测试数 | 状态 |
|---------|-------|------|
| test_login.py | 2 | ✅ PASS |
| test_my_data.py | 1 | ✅ PASS |
| test_my_data_table.py | 3 | ⏳ 待实现 |
| test_my_data_form.py | 1 | ⏳ 待实现 |
| test_teacher_data_query.py | 1 | ✅ PASS |
| test_basic_info.py | 2 | ⏳ 待实现 |

### 测试场景映射

| 场景 ID | 模块 | 说明 | 状态 |
|---------|------|------|------|
| TC-MYDATA-001 | 我的数据 | 基本信息查看 | ⏳ |
| TC-MYDATA-002~005 | 我的数据 | 家庭成员 CRUD | ⏳ |
| TC-MYDATA-006~008 | 我的数据 | 博士后信息 CRUD | ⏳ |
| TC-AUDIT-001~004 | 审核流程 | 审核流程（管理员自审） | ⏳ |

---

## 🛠️ 常用命令

```bash
# 运行所有测试
pytest tests -v

# 运行特定文件
pytest tests/teacher_data_center/test_my_data.py -v

# 并行执行（推荐，天然支持 session 级复用）
pytest tests -n auto -v

# 只运行上次失败的测试
pytest tests --lf -v

# 生成 JUnit XML（CI/CD 使用）
pytest tests --output-format=junit --output-file=reports/test-results.xml -v
```

---

## 📝 关键设计决策

### 为什么 session 级登录？

| 方案 | 登录次数（11 用例）| 耗时 | 并发支持 |
|------|------------------|------|---------|
| function 级（旧） | 11 次 | ~55-110 秒 | ✅ 好 |
| **session 级（新）** | **1-2 次** | **~10-20 秒** | ✅ 好 |

### 页面状态隔离策略

session 级共享 Page 的情况下，通过**测试自主 navigate** 实现逻辑隔离：
- 每个测试开始时调用 `page.goto(base_url + target_path)` 或页面对象的 `navigate_to()`
- 不依赖 `setup` 在其他测试后留下的状态
- 不需要每个测试都打开新浏览器

### 为什么默认管理员身份？

- 教师数据中心的核心流程（申请+审批）可用同一身份完成
- `logged_in_admin` 覆盖约 90% 场景
- 只有真正需要混合身份的场景才拆分（如 T100004 申请、T100002 审核）

---

## 📌 依赖说明

### Conda 环境

```bash
# 环境位置
C:\Users\Eddie\miniconda3\envs\manti

# Python 路径
C:\Users\Eddie\miniconda3\envs\manti\python.exe
```

### 核心依赖

- pytest 9.0.2
- playwright 1.52+
- pyyaml
- pytest-xdist（并行支持）
- pytest-html（报告）

---

## 📝 更新日志

| 日期 | 更新内容 |
|------|---------|
| 2026-03-26 | 架构重构：session 级登录复用（节省 50-90 秒） |
| 2026-03-26 | 实现 pytest-xdist 并发支持 |
| 2026-03-26 | 按用户组重新组织 fixtures（logged_in_admin / logged_in_teacher） |
| 2026-03-26 | 测试自主 navigate 设计原则，移除跨测试状态依赖 |
| 2026-03-25 | 重构目录结构（origin_test_cases / analysis_test_cases_md） |
| 2026-03-25 | 生成测试场景文档 `my_data_test_case.md` |
| 2026-03-25 | 新增 `test_my_data_table.py` 和 `test_my_data_form.py` |
| 2026-03-25 | 完善证据收集系统（视频/截图/Trace/HTML） |

---

**有问题随时问！**
