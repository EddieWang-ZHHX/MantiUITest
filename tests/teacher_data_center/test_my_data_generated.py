# tests/teacher_data_center/test_my_data.py

import pytest
from pages.teacher_data_center.my_data_page import MyDataPage

@pytest.mark.p1
def test_view_my_data(page, logged_in_user):
    """测试查看我的数据"""
    # ⭐ PageExplorer.login() 已在 logged_in_user fixture 中调用
    # ⭐ 装饰器自动监控
    
    my_data_page = MyDataPage(page)
    my_data_page.open()
    
    # 验证页面加载
    assert my_data_page.is_loaded(), "页面加载失败"
    
    # ⭐ 如果测试失败，装饰器会自动记录失败上下文
    # ⭐ 连续失败 3 次后，LLM 会分析原因并生成改进代码
