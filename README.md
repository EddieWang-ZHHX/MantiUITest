# 教师数据中心 UI 自动化测试框架

> **专业的、可审计的 UI 自动化测试框架**  
> 基于 Playwright + Python + Pytest，支持完整的证据收集（视频/截图/Trace）

---

## 📊 项目概览

| 项目信息 | 详情 |
|---------|------|
| **测试系统** | 教师数据中心 (Teacher Data Center) |
| **系统 URL** | http://172.16.34.104:7777/dataapp/ |
| **测试框架** | Playwright + Python + Pytest |
| **Python 版本** | 3.12.12 (Conda 环境：manti) |
| **架构模式** | Page Object Model (POM) |
| **证据收集** | 视频录制 + 截图 + Playwright Trace + 详细日志 |
| **测试用例来源** | XMind 测试用例（46 个：35 P1, 8 P2, 3 废弃） |

---

## 🎯 项目目标

### 核心目标
1. **自动化执行 UAT 测试用例** - 将 XMind 测试用例转化为可执行的自动化测试
2. **提高测试效率** - 减少重复手工测试，支持快速回归
3. **提供可审计的证据** - 每次测试都有完整的证据链（视频/截图/Trace）
4. **支持多环境** - 通过配置轻松切换测试/生产环境

### 测试范围
- ✅ 登录功能
- ⏳ 我的数据（个人档案）
- ⏳ 教师数据查询
- ⏳ 教师列表管理
- ⏳ 数据比对
- ⏳ 模型配置
- ⏳ 数据权限管理

---

## 🚀 快速开始（5 分钟上手）

### 前置条件

- ✅ Python 3.12+ (使用 Conda 环境 `manti`)
- ✅ 已安装 Playwright

### 1. 激活环境并运行测试

```bash
# 激活 Conda 环境
conda activate manti

# 进入项目目录
cd C:\11_UITest

# 运行所有登录测试
C:\Users\Eddie\miniconda3\envs\manti\python.exe -m pytest tests/test_00_login.py -v

# 运行所有测试
C:\Users\Eddie\miniconda3\envs\manti\python.exe -m pytest -v
```

### 2. 查看测试报告

```bash
# 打开 HTML 报告
start reports\report.html

# 查看测试证据（Trace）
C:\Users\Eddie\miniconda3\envs\manti\python.exe -m playwright show-trace reports/evidence/<测试名称>/trace.zip

# 查看测试视频
start reports\evidence\<测试名称>\video.webm
```

### 3. 查看日志

```bash
# 查看最新日志
Get-Content logs\test.log -Tail 50

# 或用记事本打开
notepad logs\test.log
```

---

## 📁 完整项目结构

```
C:\11_UITest/
│
├── 📘 文档与说明
│   ├── README.md                 # 📍 本文档（项目总览）
│   ├── QUICKSTART.md             # 快速开始指南
│   └── docs/                     # 详细文档
│       ├── 页面分析规范.md        # 📋 页面分析 SOP（重要！）
│       └── 页面分析/             # 每个页面的详细分析
│           └── 登录页面分析.md
│
├── ⚙️ 配置
│   ├── config/
│   │   ├── config.yaml           # 主配置（URL、证据收集等）
│   │   └── settings.py           # 配置加载逻辑
│   ├── pytest.ini                # Pytest 配置
│   └── requirements.txt          # Python 依赖
│
├── 📄 页面对象模型 (POM)
│   ├── pages/
│   │   ├── base_page.py          # 页面基类（通用方法）
│   │   ├── common/               # 通用页面
│   │   │   └── login_page.py     # 登录页面
│   │   └── teacher_data_center/  # 教师数据中心页面
│   │       └── my_data_page.py   # 我的数据页面
│   └── test_data/                # 测试数据
│       └── accounts.yaml         # 测试账号配置
│
├── 🧪 测试用例
│   ├── tests/
│   │   ├── conftest.py           # Pytest fixtures + 证据收集
│   │   ├── test_00_login.py      # 登录测试（2 个用例）
│   │   ├── test_01_my_data.py    # 我的数据测试（2 个用例）
│   │   └── README.md             # 测试编写指南
│   └── pytest.ini                # Pytest 配置
│
├── 🔧 工具类
│   ├── utils/
│   │   ├── browser_manager.py    # 🎥 浏览器管理（支持视频/Trace 录制）
│   │   └── logger.py             # 日志系统
│   └── setup.bat                 # 一键安装脚本
│
├── 📊 测试报告与证据
│   ├── reports/
│   │   ├── report.html           # HTML 测试报告
│   │   ├── README.md             # 证据查看指南
│   │   └── evidence/             # 📸 测试证据（每个测试的证据包）
│   │       ├── test_login_success/
│   │       │   ├── video.webm    # 测试视频
│   │       │   ├── trace.zip     # Playwright Trace（最详细证据）
│   │       │   ├── screenshot_failed.png  # 失败截图
│   │       │   └── page_failed.html       # 失败页面 HTML
│   │       └── ...
│   └── logs/
│       └── test.log              # 测试执行日志
│
└── 🧹 其他
    ├── .gitignore                # Git 忽略配置
    └── .pytest_cache/            # Pytest 缓存（自动生成）
```

---

## 🎯 核心特性

### 1. 完整的证据收集系统 🔥

**每次测试都会自动收集证据**：

| 证据类型 | 说明 | 查看方式 |
|---------|------|---------|
| 🎥 **视频录制** | 完整测试执行过程 | 直接用播放器打开 `video.webm` |
| 📸 **失败截图** | 测试失败时的全页面截图 | 打开 `screenshot_failed.png` |
| 📄 **页面 HTML** | 失败时的完整 DOM | 浏览器打开 `page_failed.html` |
| 🔍 **Playwright Trace** | ⭐ 最详细证据，包含每个操作的快照、网络请求、控制台日志 | `playwright show-trace trace.zip` |
| 📝 **详细日志** | 每个测试步骤、浏览器控制台、错误信息 | 查看 `logs/test.log` |

**配置证据收集**（`config/config.yaml`）：
```yaml
evidence:
  video: on_failure      # always / on_failure / never
  screenshot: on_failure # always / on_failure / never
  page_html: on_failure  # always / on_failure / never
  trace: on_failure      # always / on_failure / never
```

### 2. Page Object Model (POM)

- **易于维护** - 页面变化只需修改页面对象
- **代码复用** - 通用方法在基类中实现
- **清晰分层** - 测试用例只关心业务逻辑

### 3. 专业的页面分析流程

**严格遵守 SOP**（详见 `docs/页面分析规范.md`）：

```
打开页面 → 分析结构 → 提取定位器 → 编写文档 → 编写代码 → 验证测试
```

**绝不猜测元素定位器！** 每个定位器都有实际页面依据。

### 4. 灵活的配置系统

- **多环境支持** - 通过 `config.yaml` 轻松切换测试/生产环境
- **测试数据分离** - 账号配置在 `test_data/accounts.yaml`
- **可定制的日志** - 支持不同日志级别

---

## 📖 重要文档导航

### 📘 新手必读
1. **[QUICKSTART.md](QUICKSTART.md)** - 5 分钟快速上手
2. **[tests/README.md](tests/README.md)** - 如何编写测试用例
3. **[reports/README.md](reports/README.md)** - 如何查看测试报告和证据

### 📋 开发规范
1. **[docs/页面分析规范.md](docs/页面分析规范.md)** - ⭐ 页面分析 SOP（必须遵守！）
2. **[docs/页面分析/登录页面分析.md](docs/页面分析/登录页面分析.md)** - 登录页面详细分析（示例）

### 🔧 技术文档
1. **[config/config.yaml](config/config.yaml)** - 配置说明
2. **[requirements.txt](requirements.txt)** - 依赖列表

---

## 🧪 测试用例状态

### 已完成
| 测试文件 | 用例数 | 状态 | 说明 |
|---------|-------|------|------|
| `test_00_login.py` | 2 | ✅ 通过 1 个，⏳ 待修复 1 个 | 登录成功测试通过，错误密码测试待修复 |
| `test_01_my_data.py` | 2 | ⏳ 待运行 | 已编写，待网络恢复后运行 |

### 待开发（来自 XMind）
| 模块 | P1 用例数 | P2 用例数 | 优先级 |
|------|---------|---------|--------|
| 我的数据 | 3 | 1 | ⭐⭐⭐ |
| 教师数据查询 | 8 | 2 | ⭐⭐⭐ |
| 教师列表管理 | 7 | 2 | ⭐⭐ |
| 数据比对 | 7 | 2 | ⭐⭐ |
| 模型配置 | 5 | 1 | ⭐ |
| 数据权限管理 | 5 | 0 | ⭐ |

**总计**: 46 个用例（35 P1, 8 P2, 3 废弃）

---

## 🛠️ 常用命令

### 运行测试
```bash
# 运行所有测试
pytest -v

# 运行特定测试文件
pytest tests/test_00_login.py -v

# 运行特定测试类
pytest tests/test_00_login.py::TestLogin -v

# 运行特定测试方法
pytest tests/test_00_login.py::TestLogin::test_login_success -v

# 失败后重试
pytest --lf

# 并行执行（加速）
pytest -n 4
```

### 查看报告
```bash
# 打开 HTML 报告
start reports\report.html

# 查看 Trace
C:\Users\Eddie\miniconda3\envs\manti\python.exe -m playwright show-trace reports/evidence/<测试名称>/trace.zip

# 查看视频
start reports\evidence\<测试名称>\video.webm

# 查看日志
Get-Content logs\test.log -Tail 50
```

### 调试
```bash
# 慢速执行（便于观察）
pytest --headed --slowmo=1000

# 打开 Playwright Inspector
set DEBUG=pw:api
pytest tests/test_00_login.py

# 只运行失败的测试
pytest --lf
```

---

## 🔧 环境配置

### Python 环境
```bash
# 使用 Conda 环境 manti
conda activate manti

# Python 版本
python --version  # Python 3.12.12

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 测试系统配置
编辑 `config/config.yaml`：
```yaml
test:
  base_url: http://172.16.34.104:7777/dataapp
  
evidence:
  video: on_failure
  screenshot: on_failure
  trace: on_failure
```

### 测试账号配置
编辑 `test_data/accounts.yaml`：
```yaml
accounts:
  valid:
    username: T100002
    password: wisedu@1
    verify_code: "2222"
  invalid:
    username: T100002
    password: wrong_password
```

---

## 📊 测试报告示例

### HTML 报告
打开 `reports/report.html` 查看：
- ✅ 测试通过/失败状态
- 📊 执行时间统计
- 📝 错误详情
- 🔗 证据目录链接

### Playwright Trace（推荐 🔥）
```bash
C:\Users\Eddie\miniconda3\envs\manti\python.exe -m playwright show-trace reports/evidence/test_login_success/trace.zip
```

**Trace 查看器提供**：
- 📸 每个操作的截图
- 🌐 网络请求记录
- 💬 控制台日志
- ⏱️ 时间线导航
- 📄 DOM 快照

**这是最强大的调试和审计工具！**

---

## 🎯 最佳实践

### 1. 页面分析先行
**永远不要猜测元素定位器！**
```
打开页面 → 分析结构 → 编写分析文档 → 编写代码 → 验证
```

### 2. 证据收集
- 开发阶段：`evidence.trace: on_failure`
- 正式测试：`evidence.trace: always`
- 定期清理旧证据

### 3. 测试用例设计
- 每个测试独立运行
- 使用有意义的测试名称
- 包含清晰的步骤和预期结果
- 数据驱动（使用 `test_data/` 中的配置）

### 4. 维护
- 页面变化时更新页面对象
- 定期更新页面分析文档
- 清理旧的测试报告和日志

---

## 🐛 常见问题

### Q: 测试失败怎么办？
**A**: 
1. 查看 HTML 报告了解错误信息
2. 打开 Trace 回放测试过程
3. 查看失败截图和页面 HTML
4. 检查日志文件
5. 对比页面分析文档，确认定位器是否正确

### Q: 如何调试测试？
**A**:
```bash
# 慢速执行
pytest --headed --slowmo=1000

# 打开 Inspector
set DEBUG=pw:api
pytest tests/test_xxx.py

# 只运行失败的测试
pytest --lf
```

### Q: 如何添加新页面的测试？
**A**:
1. 阅读 `docs/页面分析规范.md`
2. 分析新页面，编写 `docs/页面分析/XXX 页面分析.md`
3. 创建页面对象 `pages/teacher_data_center/xxx_page.py`
4. 编写测试用例 `tests/test_xxx.py`
5. 运行测试验证

### Q: 如何切换测试环境？
**A**: 编辑 `config/config.yaml`，修改 `base_url` 即可。

---

## 📞 需要帮助？

### 文档资源
- 📘 [Playwright 官方文档](https://playwright.dev/python/)
- 📘 [Pytest 官方文档](https://docs.pytest.org/)
- 📋 [页面分析规范](docs/页面分析规范.md)
- 📋 [证据查看指南](reports/README.md)

### 项目文档
- [快速开始](QUICKSTART.md)
- [测试编写指南](tests/README.md)
- [登录页面分析](docs/页面分析/登录页面分析.md)

---

## 📝 更新日志

| 日期 | 更新内容 | 更新人 |
|------|---------|--------|
| 2026-03-24 | 创建完整项目框架 | Manti |
| 2026-03-24 | 实现证据收集系统（视频/Trace/截图） | Manti |
| 2026-03-24 | 制定页面分析规范（SOP） | Manti |
| 2026-03-24 | 完成登录页面测试（1 通过 1 待修复） | Manti |
| 2026-03-24 | 重写 README，增加项目总览和文档导航 | Manti |

---

**专业的 UI 自动化测试，从正确的流程开始！** 🦐

---

## 🎯 下一步

1. ✅ **登录测试** - 修复错误密码测试
2. ⏳ **我的数据测试** - 运行并验证
3. ⏳ **教师数据查询测试** - 开发新页面测试
4. ⏳ **完善证据系统** - 优化 Trace 和日志
5. ⏳ **持续集成** - 配置 CI/CD 自动执行

**开始自动化测试吧！** 🚀
