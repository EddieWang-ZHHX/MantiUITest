import sys
sys.path.insert(0, r'C:\Users\Eddie\lobsterai\project\.learnings\tools\current')

from ocr_engine import LocalOCR

print("=== 本地 OCR 调试 ===\n")

local = LocalOCR()
print(f"Tesseract 路径: {local.tesseract_path}")

# 直接测试 pytesseract
import pytesseract
from PIL import Image

tesseract_exe = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseract_exe

# 列出可用语言
print("\n检查语言包:")
import os
tessdata_dir = os.path.dirname(pytesseract.pytesseract.tesseract_cmd)
if not tessdata_dir.endswith('tessdata'):
    tessdata_dir = os.path.join(os.path.dirname(tessdata_dir), 'tessdata')
print(f"Tessdata 目录: {tessdata_dir}")
if os.path.exists(tessdata_dir):
    traineddata = [f for f in os.listdir(tessdata_dir) if f.endswith('.traineddata')]
    print(f"语言包: {traineddata}")

# 测试英文识别
test_image = r'C:\11_UITest\reports\evidence\test_login_success\screenshot.png'
print(f"\n测试图片: {test_image}")

try:
    # 只用英文
    text = pytesseract.image_to_string(Image.open(test_image), lang='eng')
    print(f"\n英文识别结果:\n{text[:200]}")
except Exception as e:
    print(f"\n英文识别错误: {e}")

try:
    # 只用中文
    text_cn = pytesseract.image_to_string(Image.open(test_image), lang='chi_sim')
    print(f"\n中文识别结果:\n{text_cn[:200]}")
except Exception as e:
    print(f"\n中文识别错误: {e}")
