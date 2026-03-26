# 测试用例命名规范

## 1. 文件命名

```
test_<模块>.py
test_<模块>_<子模块>.py
```

**规则**：
- 模块名用下划线分隔
- 子模块可选，用于区分不同功能组
- 一个文件只包含一个模块的测试

**示例**：
```
tests/
├── test_login.py                      # 登录模块
├── test_teacher_query.py              # 教师数据查询模块
├── test_teacher_manage.py             # 教师数据管理模块
├── test_my_data.py                    # 我的数据模块
├── test_model_permission.py            # 模型权限模块
├── test_data_compare.py               # 数据对比模块
└── test_audit_workflow.py            # 审核流程模块
```

---

## 2. 测试类命名

```
Test<模块><子模块>
```

**规则**：
- PascalCase 格式
- 子模块用 CamelCase 拼接

**示例**：
```python
class TestLogin:                      # 登录
class TestMyDataFamilyMember:         # 我的数据-家庭成员
class TestMyDataPostdoc:             # 我的数据-博士后信息
class TestTeacherQuery:              # 教师数据查询
class TestTeacherManage:             # 教师数据管理
class TestModelPermission:            # 模型权限
class TestAuditWorkflow:             # 审核流程
```

---

## 3. 测试方法命名

```
test_<操作>_<验证点>
```

**操作动词**：
| 动词 | 含义 |
|------|------|
| `add` | 新增 |
| `edit` | 编辑 |
| `delete` | 删除 |
| `query` | 查询 |
| `import` | 导入 |
| `export` | 导出 |
| `audit_approve` | 审核通过 |
| `audit_reject` | 审核驳回 |

**验证点后缀**：
| 后缀 | 含义 |
|------|------|
| `_success` | 操作成功 |
| `_fail` | 操作失败 |
| `_visible` | 可见性 |
| `_count` | 数量验证 |
| `_permission` | 权限验证 |

**示例**：
```python
# 家庭成员 CRUD
def test_family_member_add_success(self):      # 新增成功
def test_family_member_edit_success(self):     # 编辑成功
def test_family_member_delete_success(self):    # 删除成功
def test_family_member_query_by_name(self):    # 按姓名查询

# 博士后信息 CRUD
def test_postdoc_add_success(self):            # 新增成功
def test_postdoc_edit_success(self):           # 编辑成功
def test_postdoc_delete_success(self):         # 删除成功

# 审核流程
def test_audit_new_edit_shows_immediately(self):      # 新增审核-自己立即可见
def test_audit_new_edit_shows_to_others_after_approve(self):  # 新增审核-他人审核后可见
def test_audit_edit_shows_to_self_immediately(self):         # 编辑审核-自己立即可见
def test_audit_edit_shows_to_others_after_approve(self):     # 编辑审核-他人审核后可见
def test_delete_no_audit(self):                              # 删除不审核
```

---

## 4. TC ID 映射

在测试方法的 docstring 中保留 TC ID：

```python
def test_family_member_add_success(self, logged_in_as_teacher):
    """
    TC-MYDATA-002: 家庭成员新增
    
    前置条件: 教师身份登录，进入家庭成员模块
    验证点:
      1. 新增后数据列表增加一条
      2. 数据内容正确
    """
```

---

## 5. Fixture 命名

| Fixture | 用途 | 身份 |
|---------|------|------|
| `login_page` | 登录页对象 | 未登录 |
| `logged_in_user` | 已登录用户 | 信息中心管理员 |
| `logged_in_as_teacher` | 教师身份 | 教师 |

---

## 6. 测试文件模板

```python
"""
<模块名称>测试

TC ID 映射:
  - TC-XXX-001: 功能描述
  - TC-XXX-002: 功能描述
"""
import pytest
from utils.logger import logger


class Test<模块><子模块>:
    """<模块描述>"""
    
    def test_<操作>_<验证点>(self, logged_in_as_teacher):
        """
        TC-XXX-001: <用例描述>
        
        前置条件: <前置条件>
        验证点:
          1. <验证点1>
          2. <验证点2>
        """
        logger.info("========== 开始测试: <用例描述> ==========")
        
        # TODO: 测试步骤
        
        logger.info("========== 测试通过 ==========")
```

---

## 7. 命名检查清单

新建测试用例时检查：
- [ ] 文件名符合 `test_<模块>.py` 格式
- [ ] 测试类名符合 `Test<模块><子模块>` 格式
- [ ] 测试方法名符合 `test_<操作>_<验证点>` 格式
- [ ] docstring 包含 TC ID 和验证点
- [ ] 使用正确的 fixture（`logged_in_user` vs `logged_in_as_teacher`）
