# 测试追踪表

> **维护者**: Manti  
> **更新时间**: 2026-03-25

---

## 目录结构

```
C:\11_UITest\
├── docs/
│   ├── origin_test_cases/                    # 原始测试用例
│   │   └── teacher_data_center/
│   └── analysis_test_cases_md/              # 分析后的测试场景
│       └── teacher_data_center/
│           └── my_data_test_case.md
├── tests/                                    # 测试脚本
│   ├── common/
│   │   └── test_login.py
│   └── teacher_data_center/
│       ├── test_my_data.py
│       ├── test_my_data_table.py
│       ├── test_my_data_form.py
│       ├── test_my_data_basic_info.py
│       └── test_teacher_data_query.py
└── TEST_TRACKER.md
```

---

## 工作流程

```
1. 你把测试用例（Word/XMind）复制到 docs/origin_test_cases/teacher_data_center/
2. 我读取并分析
3. 我在 docs/analysis_test_cases_md/teacher_data_center/ 生成测试场景 md
4. 我在 tests/teacher_data_center/ 实现测试脚本
5. 我在 TEST_TRACKER.md 更新状态
```

---

## 当前测试状态

| 测试 | 状态 | 耗时 |
|------|------|------|
| test_login_success | ✅ PASS | 1.9s |
| test_login_fail | ✅ PASS | 1.0s |
| test_my_data_page_visible | ✅ PASS | 4.7s |
| test_postdoc_add | ✅ PASS | 10.4s |
| test_postdoc_edit | ✅ PASS | 11.6s |
| test_postdoc_delete | ✅ PASS | 11.4s |
| test_family_member_add | ✅ PASS | 15.3s |
| test_family_member_edit | ✅ PASS | 20.2s |
| test_family_member_delete | ✅ PASS | 45.1s |
| test_teacher_query_page_visible | ✅ PASS | 1.9s |

**通过率**: 10/10 (100%)  
**总耗时**: 4 分钟

---

## 场景映射表

### 已实现 ✅

| 场景 ID | 测试脚本 | 状态 |
|---------|---------|------|
| TC-100269 | test_my_data.py::test_my_data_page_visible | ✅ |
| TC-MYDATA-002 | test_my_data_table.py::test_family_member_add | ✅ |
| TC-MYDATA-003 | test_my_data_table.py::test_family_member_edit | ✅ |
| TC-MYDATA-004 | test_my_data_table.py::test_family_member_delete | ✅ |
| TC-MYDATA-005 | test_my_data_table.py::test_family_member_persistence | ✅ |
| TC-MYDATA-006 | test_my_data_form.py::test_postdoc_add | ✅ |
| TC-MYDATA-007 | test_my_data_form.py::test_postdoc_edit | ✅ |
| TC-MYDATA-008 | test_my_data_form.py::test_postdoc_delete | ✅ |

### 待实现

| 场景 ID | 说明 | 状态 |
|---------|------|------|
| TC-MYDATA-009~012 | 异常场景 | ⏳ |
| TC-AUDIT-001~004 | 审核流程 | ⏳ |

---

## 审核流程测试设计

### TC-AUDIT-001: 教师新增数据 → 管理员审核通过

```
1. 教师登录
2. 教师进入"我的数据" → 新增家庭成员
3. 填写表单 → 提交
4. 记录数据内容
5. 教师登出
6. 管理员登录（切换身份）
7. 进入"审核管理"页面
8. 找到待审核数据
9. 点击"通过"
10. 管理员登出
11. 教师登录
12. 进入"我的数据"
13. 验证数据可见
```

### TC-AUDIT-002: 教师编辑数据 → 管理员审核拒绝

```
1. 教师登录
2. 教师进入"我的数据" → 新增家庭成员
3. 提交并审核通过
4. 教师登出
5. 管理员登录
6. 教师登录
7. 编辑家庭成员 → 提交（状态变为"待审核"）
8. 教师登出
9. 管理员登录
10. 进入"审核管理"
11. 找到待审核数据 → 点击"拒绝"
12. 管理员登出
13. 教师登录
14. 验证数据内容未变化（还是旧内容）
```

### TC-AUDIT-003: 管理员删除数据

```
1. 管理员登录
2. 进入"我的数据"
3. 新增一条数据
4. 直接删除
5. 验证数据已删除
```

### TC-AUDIT-004: 教师删除自己的待审核数据

```
1. 教师登录
2. 进入"我的数据"
3. 新增家庭成员 → 提交（状态为"待审核"）
4. 删除该数据（无需审核，直接删除）
5. 进入"审核管理"
6. 验证待审核列表中无该数据
```

---

## 最近更新

| 日期 | 更新内容 |
|------|---------|
| 2026-03-25 | 10/10 测试全部通过 (dropdown_helper.py 解决中文编码问题) |
| 2026-03-25 | 目录结构调整为 origin_test_cases / analysis_test_cases_md |
| 2026-03-25 | 生成测试场景文档 my_data_test_case.md |
| 2026-03-25 | 修复 logged_in_as_teacher fixture 身份切换 |
