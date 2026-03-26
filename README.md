# 教师数据中心 UI 自动化测试框架

> 基于 Playwright + Python + Pytest，支持完整的证据收集（视频/截图/Trace）

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
│   └── config.yml              # 主配置
├── pages/
│   ├── base_page.py           # 页面基类
│   ├── common/
│   │   └── login_page.py     # 登录页面
│   └── teacher_data_center/
│       └── my_data_page.py   # 我的数据页面
├── tests/
│   ├── conftest.py           # Pytest fixtures + 证据收集
│   ├── common/               # common 模块
│   │   ├── test_00_login.py
│   │   └── test_00_login_with_identity.py
│   └── teacher_data_center/  # teacher_data_center 模块
│       └── test_01_my_data.py
├── utils/
│   ├── browser_manager.py    # 浏览器管理
│   ├── logger.py            # 日志
│   └── test_formatter.py   # 结果格式化
├── scripts/                  # 运维脚本
│   ├── check_naming_rules.py
│   └── evidence_cleaner.py
├── reports/
│   ├── report.html          # HTML 报告
│   └── evidence/           # 证据（按模块分组）
│       ├── common/
│       └── teacher_data_center/
└── docs/                    # 详细文档
    ├── 页面分析规范.md
    └── 页面分析/
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
| [config/config.yml](config/config.yml) | 配置文件说明 |

---

## 🛠️ 常用命令

```bash
# 查看 Trace（最详细证据）
playwright show-trace evidence/common/test_login_success/trace.zip

# 慢速调试
pytest --headed --slowmo=1000

# 只跑失败的测试
pytest --lf

# 检查命名规范
python scripts/check_naming_rules.py
```

---

**有问题？查看 reports/README.md 或 tests/README.md** 🦐
