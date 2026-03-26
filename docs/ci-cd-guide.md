# CI/CD 集成指南

**文档版本**: v1.0
**更新日期**: 2026-03-24

---

## 🎯 概述

本框架支持完整的 CI/CD 集成，提供：
- **多格式输出** (JSON, JUnit XML, CSV)
- **并行执行** (pytest-xdist)
- **快速失败** (--maxfail)
- **无状态设计** (可重复执行)

---

## 🚀 快速开始

### 1. 基本 CI 命令

```bash
# 使用默认配置运行
pytest tests/ -v

# 生成 JUnit XML 报告 (用于 Jenkins/GitLab CI/GitHub Actions)
pytest tests/ --junit-xml=reports/test-results.xml

# 使用 JSON 输出
pytest tests/ --output-format=json --output-file=reports/results.json

# 快速失败模式 (连续 3 次失败后停止)
pytest tests/ --maxfail=3
```

### 2. GitHub Actions 示例

```yaml
# .github/workflows/test.yml
name: UI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Run tests
        run: |
          pytest tests/ \
            --junit-xml=reports/test-results.xml \
            --html=reports/report.html \
            --output-format=junit
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-reports
          path: reports/
```

### 3. GitLab CI 示例

```yaml
# .gitlab-ci.yml
stages:
  - test

ui-tests:
  stage: test
  image: python:3.12
  
  before_script:
    - pip install -r requirements.txt
    - playwright install chromium --with-deps
  
  script:
    - pytest tests/ --junit-xml=reports/test-results.xml --html=reports/report.html
  
  artifacts:
    when: always
    reports:
      junit: reports/test-results.xml
    paths:
      - reports/
```

### 4. Jenkins 示例

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('UI Tests') {
            steps {
                bat '''
                    pip install -r requirements.txt
                    playwright install chromium
                    pytest tests/ --junit-xml=reports/test-results.xml
                '''
            }
            post {
                always {
                    junit 'reports/test-results.xml'
                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, 
                                 reportDir: 'reports', reportFiles: 'report.html', 
                                 reportName: 'UI Test Report'])
                }
            }
        }
    }
}
```

---

## 📊 输出格式

### JUnit XML (推荐用于 CI/CD)

```bash
# 生成 JUnit XML 报告
pytest tests/ --junit-xml=reports/test-results.xml
```

**输出示例**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="UITestSuite" tests="4" failures="1" errors="0" skipped="0" time="23.456">
  <testcase classname="test_00_login.TestLogin" name="test_login_success" time="5.123"/>
  <testcase classname="test_00_login.TestLogin" name="test_login_wrong_password" time="4.567">
    <failure message="AssertionError: 密码错误时应该提示错误信息">
      # 错误详情...
    </failure>
  </testcase>
</testsuite>
```

### JSON 格式

```bash
# 生成 JSON 报告
pytest tests/ --output-format=json --output-file=reports/results.json
```

**输出示例**:
```json
[
  {
    "name": "test_login_success",
    "status": "passed",
    "duration": 5.123,
    "message": null,
    "timestamp": "2026-03-24T14:30:00"
  },
  {
    "name": "test_login_wrong_password",
    "status": "failed",
    "duration": 4.567,
    "message": "密码错误时应该提示错误信息",
    "timestamp": "2026-03-24T14:30:05"
  }
]
```

### CSV 格式

```bash
# 生成 CSV 报告
pytest tests/ --output-format=csv --output-file=reports/results.csv
```

---

## ⚡ 性能优化

### 并行执行

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 使用 4 个 worker 并行执行
pytest tests/ -n 4

# 自动检测 CPU 核心数
pytest tests/ -n auto
```

### 测试分组

```python
# tests/test_00_login.py
import pytest

@pytest.mark.smoke
def test_login_success():
    """冒烟测试 - 快速验证"""
    pass

@pytest.mark.regression
def test_login_all_cases():
    """回归测试 - 完整验证"""
    pass

# 运行特定分组
pytest tests/ -m smoke      # 只运行冒烟测试
pytest tests/ -m regression # 只运行回归测试
```

### 快速失败

```bash
# 连续 3 次失败后停止
pytest tests/ --maxfail=3

# 失败后立即停止 (用于调试)
pytest tests/ -x
```

---

## 🔧 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CI` | 是否在 CI 环境中 | `false` |
| `PYTEST_XDIST_WORKER` | pytest-xdist worker ID | `master` |
| `BASE_URL` | 测试环境 URL | config.yaml 中的值 |

### CI 环境检测

框架自动检测 CI 环境并优化输出：

```python
import os

if os.environ.get("CI") == "true":
    # CI 环境：生成 JUnit XML
    # 减少控制台输出
    # 启用快速失败
```

---

## 📁 报告结构

```
reports/
├── test-results.xml      # JUnit XML (CI/CD)
├── results.json          # JSON 格式
├── results.csv           # CSV 格式
├── report.html           # HTML 报告
└── evidence/             # 测试证据
    ├── test_xxx/
    │   ├── video.webm
    │   ├── trace.zip
    │   ├── screenshot.png
    │   └── page.html
    └── ...
```

---

## ✅ 最佳实践

### 1. 分离测试环境

```bash
# 使用环境变量覆盖配置
BASE_URL=http://test.example.com pytest tests/
```

### 2. 失败时收集完整证据

```yaml
# GitHub Actions
- name: Upload evidence on failure
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: test-evidence
    path: reports/evidence/
```

### 3. 定期清理旧证据

```bash
# 保留最近 30 天的证据
find reports/evidence -mtime +30 -type d -exec rm -rf {} +
```

### 4. 测试优先级

```bash
# 优先运行 P1 测试
pytest tests/ -m p1 -v

# 然后运行 P2
pytest tests/ -m p2 -v
```

---

## 🔍 故障排除

### 问题：Jenkins 无法找到测试结果

**解决方案**: 确保 JUnit XML 路径正确

```groovy
junit 'reports/test-results.xml'  // 相对于工作目录
```

### 问题：并行测试导致数据库冲突

**解决方案**: 每个测试使用独立的数据库 schema

```python
@pytest.fixture(scope="function")
def isolated_db():
    """每个测试使用独立的数据库"""
    db_name = f"test_{uuid.uuid4().hex[:8]}"
    yield db_name
    # 清理
```

### 问题：视频录制导致 CI 存储爆炸

**解决方案**: 仅在失败时录制

```yaml
# config.yaml
evidence:
  video: on_failure  # 仅失败时录制
  trace: on_failure
```

---

## 📞 集成检查清单

- [ ] JUnit XML 输出配置正确
- [ ] GitLab CI / GitHub Actions 配置完成
- [ ] 报告上传步骤配置完成
- [ ] 证据收集配置完成
- [ ] 并行执行验证通过
- [ ] 快速失败模式验证通过
