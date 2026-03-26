import sys
sys.path.insert(0, r'C:\Users\Eddie\lobsterai\project\.learnings\tools\current')

from ocr_engine import LocalOCR

print("=== 本地 OCR 调试 ===\n")

local = LocalOCR()
print(f"Tesseract 路径: {local.tesseract_path}")
print(f"可用: {local.available}")

# 检查语言包
import os
tessdata = r"C:\Program Files\Tesseract-OCR\tessdata"
if os.path.exists(tessdata):
    files = os.listdir(tessdata)
    traineddata = [f for f in files if f.endswith('.traineddata')]
    print(f"语言包数量: {len(traineddata)}")
    for f in traineddata[:5]:
        print(f"  - {f}")
    if len(traineddata) > 5:
        print(f"  ... 等 {len(traineddata) - 5} 个")

# 测试英文识别
test_image = r'C:\11_UITest\reports\evidence\test_login_success\screenshot.png'
print(f"\n测试图片: {test_image}")

# 使用默认语言（只有英文）
result = local.recognize(test_image)
print(f"\n结果:")
print(f"  成功: {result.success}")
print(f"  错误: {result.error}")
print(f"  文字: {result.text[:200] if result.text else '(无)'}")
