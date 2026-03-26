# 🚀 快速开始指南

## 1️⃣ 安装依赖

### 方式一：使用安装脚本（推荐）
```bash
cd C:\11_UITest
setup.bat
```

### 方式二：手动安装
```bash
cd C:\11_UITest
pip install -r requirements.txt
playwright install
playwright install-deps
```

## 2️⃣ 配置测试

编辑 [`config/config.yaml`](file:///C:/11_UITest/config/config.yaml)：

```yaml
test:
  base_url: https://你的测试网站.com  # 修改为你的测试地址
  timeout: 30000

browser:
  headless: false  # true=后台运行，false=显示浏览器
```

## 3️⃣ 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_example.py

# 运行特定测试方法
pytest tests/test_example.py::TestExample::test_page_title

# 生成 HTML 报告
pytest --html=reports/report.html

# 查看报告
start reports/report.html
```

## 4️⃣ 创建你的第一个测试

### 步骤 1：创建页面对象

在 [`pages/`](file:///C:/11_UITest/pages/) 目录创建 `my_page.py`：

```python
from .base_page import BasePage

class MyPage(BasePage):
    # 定义元素定位器
    SEARCH_INPUT = "#search"
    SUBMIT_BUTTON = "#submit"
    
    def search(self, keyword):
        return (self
            .fill(self.SEARCH_INPUT, keyword)
            .click(self.SUBMIT_BUTTON))
```

### 步骤 2：创建测试用例

在 [`tests/`](file:///C:/11_UITest/tests/) 目录创建 `test_my_feature.py`：

```python
def test_search_function(my_page):
    my_page.open("/search")
    my_page.search("测试关键词")
    my_page.expect_visible(".search-results")
```

### 步骤 3：运行测试

```bash
pytest tests/test_my_feature.py -v
```

## 📋 常用命令

| 命令 | 说明 |
|------|------|
| `pytest` | 运行所有测试 |
| `pytest -v` | 详细输出 |
| `pytest -x` | 遇到第一个失败就停止 |
| `pytest -s` | 显示 print 输出 |
| `pytest -m smoke` | 运行冒烟测试 |
| `pytest -n 4` | 并行执行（4 个进程） |
| `pytest --html=report.html` | 生成 HTML 报告 |
| `pytest --alluredir=allure` | 生成 Allure 数据 |

## 🎯 项目结构说明

```
C:\11_UITest/
├── config/           # 配置文件
│   └── config.yaml   # 主配置（修改这里！）
├── pages/            # 页面对象（POM 模式）
│   ├── base_page.py  # 页面基类
│   └── example_page.py
├── tests/            # 测试用例
│   ├── conftest.py   # Pytest 配置
│   └── test_example.py
├── utils/            # 工具类
│   ├── logger.py     # 日志
│   └── browser_manager.py
├── test_data/        # 测试数据
├── reports/          # 测试报告（自动生成）
├── logs/             # 日志文件（自动生成）
└── requirements.txt  # Python 依赖
```

## 🔧 常见问题

### Q: 浏览器无法启动？
A: 运行 `playwright install` 安装浏览器

### Q: 测试超时？
A: 在 `config/config.yaml` 增加 `timeout` 值

### Q: 如何调试？
A: 在测试中加 `import pdb; pdb.set_trace()` 或使用 `--pdb` 参数

### Q: 如何截图？
A: 调用 `page.screenshot(path="debug.png")`

## 📚 学习资源

- [Playwright 官方文档](https://playwright.dev/python/)
- [Pytest 官方文档](https://docs.pytest.org/)
- [页面对象模式](https://playwright.dev/python/docs/pom)

---

**开始自动化测试吧！** 🦐

有问题随时问我！
