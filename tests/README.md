# 测试用例说明

## 📁 测试文件组织

```
tests/
├── conftest.py              # Pytest 配置和 fixtures
├── test_00_login.py         # 登录测试
├── test_01_my_data.py       # 我的数据测试
├── test_02_data_query.py    # 数据查询测试（待创建）
├── test_03_teacher_manage.py # 教师数据管理测试（待创建）
└── ...
```

## 🚀 运行测试

### 运行所有测试
```bash
cd C:\11_UITest
pytest
```

### 运行登录测试
```bash
pytest tests/test_00_login.py -v
```

### 运行我的数据测试
```bash
pytest tests/test_01_my_data.py -v
```

### 运行特定测试
```bash
pytest tests/test_00_login.py::TestLogin::test_login_success -v
```

### 生成 HTML 报告
```bash
pytest --html=reports/report.html --self-contained-html
```

### 查看报告
```bash
start reports/report.html
```

## 📝 当前测试用例

### test_00_login.py - 登录测试

| 用例 ID | 测试名称 | 优先级 | 状态 |
|--------|---------|--------|------|
| TC-LOGIN-001 | 验证登录功能正常 | P1 | ✅ 已实现 |
| TC-LOGIN-002 | 验证错误密码登录失败 | P2 | ✅ 已实现 |

### test_01_my_data.py - 我的数据测试

| 用例 ID | 测试名称 | 优先级 | 状态 |
|--------|---------|--------|------|
| TC-MYDATA-001 | 验证我的数据页面可访问 | P1 | ✅ 已实现 |
| TC-MYDATA-002 | 验证模块可以展开和收起 | P2 | ✅ 已实现 |

## 🔧 Fixtures 说明

### `login_page`
登录页面对象，用于执行登录操作。

### `logged_in_user`
已登录用户 fixture，自动执行登录，后续测试可以直接使用。

### `my_data_page`
我的数据页面对象，用于访问和操作我的数据页面。

## ⚠️ 注意事项

1. **元素定位器可能需要调整** - 当前的 CSS selectors 是猜测的，需要根据实际页面调整
2. **第一次运行可能失败** - 因为元素定位器可能不准确，需要调试
3. **查看日志** - 测试失败时查看 `logs/test.log` 了解详细信息

## 🐛 调试方法

### 1. 查看元素定位器
打开浏览器开发者工具（F12），检查实际元素的 ID/Class

### 2. 修改定位器
在对应的 page 文件中修改元素定位器：
```python
USERNAME_INPUT = "#actual_username_id"  # 修改这里
```

### 3. 重新运行测试
```bash
pytest tests/test_00_login.py -v -s
```

### 4. 截图调试
在测试中添加截图：
```python
def test_debug(page):
    page.screenshot(path="debug.png")
```

## 📊 下一步计划

1. ✅ 登录测试 - 已完成
2. ✅ 我的数据页面访问 - 已完成
3. ⏳ 数据校验测试 - 待开发
4. ⏳ 教师数据查询测试 - 待开发
5. ⏳ 教师数据管理测试 - 待开发

## 💡 提示

- 测试失败时不要慌，先查看日志和错误信息
- 元素定位器需要逐步调试，这是正常的
- 每个测试都是独立的，可以单独运行
- 使用 `-s` 参数可以看到 print 输出
- 使用 `--tb=short` 可以简化错误堆栈

---

**开始运行第一个测试吧！** 🦐
