# 测试用例编写指南

## 标准测试用例模板

每个测试用例必须包含以下结构：

```python
def test_xxx(self, page):
    """
    TC-XXX-001: 测试用例标题

    【验证方式】（必须填写 — 如何判断这个功能"工作正常"）
    验证点 1: [具体验证什么]
    验证点 2: [具体验证什么]
    验证点 3: [具体验证什么]

    前置条件:
    - 条件 1
    - 条件 2

    测试步骤:
    1. 步骤 1
    2. 步骤 2

    预期结果:
    - 结果 1
    - 结果 2

    失败自检清单 (Critical / Warning / Note):
    Critical:
      - [ ] 定位器是否在页面分析文档里验证过？
      - [ ] 预期结果是否符合实际页面能力？
    Warning:
      - [ ] 测试是否独立（不依赖其他用例的状态）？
      - [ ] 测试数据是否稳定（不会被其他测试修改）？
    Note:
      - [ ] 证据收集配置是否正确？
      - [ ] 是否有对应的页面分析文档？
    """
    # 测试代码...
```

## 为什么要写"验证方式"

> **Evidence over claims** — Superpowers 核心理念

"测试通过了"不是证据。能说清楚"**怎么验证它工作正常**"才是证据。

**错误写法**：
```python
# 验证登录成功
login_page.login("T100002", "wisedu@1", "2222")
assert login_page.is_logged_in()  # 什么叫"登录成功"？判断标准是什么？
```

**正确写法**：
```python
# 验证登录成功
login_page.login("T100002", "wisedu@1", "2222")

# 验证方式（必须全部满足）：
# 1. URL 从 /login 跳转到包含 /dataapp/ 且不含 login
# 2. 页面包含"我的数据"或"退出"按钮
# 3. 无错误提示弹窗
assert "/login" not in login_page.page.url, "URL 仍在登录页"
assert login_page.is_visible("text=退出", "退出按钮")
assert not login_page.is_visible(".error-message", "无错误提示")
```

## 验证点来源

验证点必须来自**页面分析文档**，不是猜测。

每个验证点格式：
```
验证点 N: [具体验证什么] + [在哪里找到这个验证标准]
```

示例：
```
验证点 1: 登录后 URL 跳转到 /dataapp/ (来自 docs/页面分析/登录页面分析.md "页面跳转逻辑")
验证点 2: 页面包含用户昵称或"退出"按钮 (来自页面实际渲染)
验证点 3: 30 秒内完成跳转，无 loading 一直显示 (来自性能要求)
```

## 失败自检清单

每次测试失败后，先执行自检再开始 debug：

### Critical（阻塞性问题，必须修复才能继续）
- [ ] **定位器是否在页面分析文档里验证过？**
  - 如果没有 → 先去分析页面，再继续
- [ ] **预期结果是否符合实际页面能力？**
  - 如果文档过时 → 先更新文档
- [ ] **页面是否有权限限制或特殊状态？**
  - 如果是 → 先解决权限问题

### Warning（可能导致后续问题）
- [ ] **测试是否独立（不依赖其他用例的状态）？**
  - 如果不是 → 考虑使用独立的测试数据或 teardown
- [ ] **测试数据是否会被其他测试修改？**
  - 如果会 → 使用唯一测试数据

### Note（改进项）
- [ ] **证据收集配置是否正确？** (trace: always, screenshot: always)
- [ ] **是否有对应的页面分析文档？**
- [ ] **是否有超时设置？（网络慢时需要）**

## 测试数据管理

所有测试数据必须在 `test_data/` 目录下管理，禁止硬编码：

```yaml
# test_data/accounts.yaml
accounts:
  valid:
    username: T100002
    password: wisedu@1
    verify_code: "2222"
  invalid_password:
    username: T100002
    password: wrong_password
    verify_code: "2222"
```

## 调试流程（使用 debugger.py）

```python
from utils.debugger import StructuredDebugger

def test_xxx_failure_debug(page):
    """测试失败时使用结构化 debug"""
    debugger = StructuredDebugger("test_xxx")
    debugger.collect()
    debugger.suggest_hypotheses("login")  # 或 "navigation", "assertion"
    debugger.report()
```

## 快速自检命令

```powershell
# 运行测试并自动打开 trace 查看器
pytest tests/test_00_login.py::TestLogin::test_login_success --trace

# 只运行上次失败的测试
pytest --lf

# 慢速执行（便于观察）
pytest --headed --slowmo=500
```
