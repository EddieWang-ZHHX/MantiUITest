"""
页面拆分评估工具 - 量化决策框架

使用方法:
    from utils.page_analyzer import quick_evaluate
    
    score, should_split = quick_evaluate(
        page1_url="/dataapp/login",
        page2_url="/dataapp/login#/identity",
        page1_func="登录",
        page2_func="身份选择"
    )
    
    if should_split:
        print("建议拆分")
    else:
        print("建议合并")
"""
from typing import Tuple


def quick_evaluate(page1_url: str, page2_url: str, 
                   page1_func: str, page2_func: str,
                   page1_elements: int = 10, page2_elements: int = 10,
                   page1_methods: int = 5, page2_methods: int = 5) -> Tuple[float, bool]:
    """
    快速评估两个页面是否应该拆分
    
    评分维度:
    1. URL 差异 (40% 权重)
       - 3 分：父路径不同
       - 2 分：子路径不同
       - 1 分：相同路径
    
    2. 功能独立性 (30% 权重)
       - 3 分：完全独立
       - 2 分：相关但可独立
       - 1 分：强依赖
    
    3. 元素重叠率 (20% 权重)
       - 3 分：重复率<30%
       - 2 分：重复率 30%-70%
       - 1 分：重复率>70%
    
    4. 测试独立性 (10% 权重)
       - 3 分：可独立测试
       - 2 分：需要少量前置
       - 1 分：强依赖
    
    决策阈值：总分 >= 2.5 → 拆分
    """
    
    # ===== 1. URL 差异评分 =====
    def get_parent_path(url: str) -> str:
        url = url.split('#')[0].split('?')[0]
        parts = url.strip('/').split('/')
        return '/' + parts[0] if parts else '/'
    
    parent1 = get_parent_path(page1_url)
    parent2 = get_parent_path(page2_url)
    
    if parent1 != parent2:
        url_score = 3.0
    elif page1_url != page2_url:
        url_score = 2.0
    else:
        url_score = 1.0
    
    # ===== 2. 功能独立性评分 =====
    DEPENDENCY_MAP = {
        ('登录', '身份选择'): 1.0,
        ('登录', '忘记密码'): 2.0,
        ('查询', '导出'): 2.0,
        ('查询', '编辑'): 3.0,
    }
    
    key = (page1_func, page2_func)
    reverse_key = (page2_func, page1_func)
    
    if key in DEPENDENCY_MAP:
        function_score = DEPENDENCY_MAP[key]
    elif reverse_key in DEPENDENCY_MAP:
        function_score = DEPENDENCY_MAP[reverse_key]
    else:
        function_score = 3.0
    
    # ===== 3. 元素重叠率评分 =====
    if page1_elements == 0 or page2_elements == 0:
        element_score = 2.0
    else:
        diff_ratio = abs(page1_elements - page2_elements) / max(page1_elements, page2_elements)
        if diff_ratio > 0.7:
            element_score = 3.0
        elif diff_ratio > 0.3:
            element_score = 2.0
        else:
            element_score = 1.0
    
    # ===== 4. 测试独立性评分 =====
    total_methods = page1_methods + page2_methods
    if total_methods >= 10:
        test_score = 3.0
    elif total_methods >= 5:
        test_score = 2.0
    else:
        test_score = 1.0
    
    # ===== 计算加权总分 =====
    WEIGHTS = {
        'url': 0.4,
        'function': 0.3,
        'elements': 0.2,
        'test': 0.1
    }
    
    total_score = (
        url_score * WEIGHTS['url'] +
        function_score * WEIGHTS['function'] +
        element_score * WEIGHTS['elements'] +
        test_score * WEIGHTS['test']
    )
    
    SPLIT_THRESHOLD = 2.5
    should_split = total_score >= SPLIT_THRESHOLD
    
    # ===== 打印评估报告 =====
    print("\n" + "="*60)
    print("页面拆分评估报告")
    print("="*60)
    print(f"页面 1: {page1_func} (URL: {page1_url})")
    print(f"页面 2: {page2_func} (URL: {page2_url})")
    print("-"*60)
    print(f"{'维度':<15} {'得分':<8} {'权重':<8} {'加权分':<10}")
    print("-"*60)
    print(f"{'URL 差异':<15} {url_score:<8.1f} {WEIGHTS['url']:<8.1%} {url_score * WEIGHTS['url']:<10.2f}")
    print(f"{'功能独立性':<15} {function_score:<8.1f} {WEIGHTS['function']:<8.1%} {function_score * WEIGHTS['function']:<10.2f}")
    print(f"{'元素重叠率':<15} {element_score:<8.1f} {WEIGHTS['elements']:<8.1%} {element_score * WEIGHTS['elements']:<10.2f}")
    print(f"{'测试独立性':<15} {test_score:<8.1f} {WEIGHTS['test']:<8.1%} {test_score * WEIGHTS['test']:<10.2f}")
    print("-"*60)
    print(f"{'总分':<15} {total_score:.2f}     {'阈值':<8} {SPLIT_THRESHOLD:.1f}")
    print("="*60)
    
    if should_split:
        print(f"✅ 建议：拆分（总分 {total_score:.2f} >= 阈值 {SPLIT_THRESHOLD}）")
    else:
        print(f"❌ 建议：合并（总分 {total_score:.2f} < 阈值 {SPLIT_THRESHOLD}）")
    print("="*60 + "\n")
    
    return total_score, should_split


if __name__ == "__main__":
    print("示例 1: 登录页 vs 身份选择")
    quick_evaluate(
        page1_url="/dataapp/login",
        page2_url="/dataapp/login#/identity",
        page1_func="登录",
        page2_func="身份选择",
        page1_elements=6,
        page2_elements=4,
        page1_methods=5,
        page2_methods=3
    )
    
    print("\n示例 2: 登录页 vs 我的数据页")
    quick_evaluate(
        page1_url="/dataapp/login",
        page2_url="/dataapp/index#/myarchive",
        page1_func="登录",
        page2_func="我的数据",
        page1_elements=6,
        page2_elements=15,
        page1_methods=5,
        page2_methods=10
    )
    
    print("\n示例 3: 数据查询页 vs 数据导出页")
    quick_evaluate(
        page1_url="/dataapp/query",
        page2_url="/dataapp/export",
        page1_func="数据查询",
        page2_func="数据导出",
        page1_elements=12,
        page2_elements=8,
        page1_methods=8,
        page2_methods=5
    )
