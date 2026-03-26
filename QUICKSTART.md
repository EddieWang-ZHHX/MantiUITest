# 快速开始指南

## 1️⃣ 运行测试

```bash
Set-Location C:\11_UITest
C:\Users\Eddie\miniconda3\Scripts\conda.exe run -n manti pytest tests -v
```

## 2️⃣ 查看报告

```bash
# HTML 报告（包含视频/截图/Trace链接）
start C:\11_UITest\reports\report.html

# 证据目录
C:\11_UITest\reports\evidence\
```

## 3️⃣ 当前测试状态

| 测试 | 状态 |
|------|------|
| test_login_success | ✅ |
| test_login_fail | ✅ |
| test_my_data_page_visible | ✅ |
| test_postdoc_add | ❌ |
| test_postdoc_edit | ❌ |
| test_postdoc_delete | ❌ |

## 4️⃣ 测试场景文档

```
docs/analysis_test_cases_md/teacher_data_center/my_data_test_case.md
```

## 5️⃣ 添加新测试

1. 参考测试场景文档
2. 在 `tests/teacher_data_center/` 创建测试文件
3. 使用 `logged_in_as_teacher` 或 `logged_in_user` fixture

## 6️⃣ 常用命令

```bash
# 运行特定文件
C:\Users\Eddie\miniconda3\Scripts\conda.exe run -n manti pytest tests\common\test_login.py -v

# 只运行失败的测试
C:\Users\Eddie\miniconda3\Scripts\conda.exe run -n manti pytest tests --lf -v
```

---

**详细文档见 [README.md](README.md)**
