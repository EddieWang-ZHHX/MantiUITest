"""
OCR 文字识别辅助工具

集成到 11_UITest 框架，提供简单的 OCR 识别接口。

支持引擎：
- 百度 OCR（高精度，需要 API Key）
- 本地 Tesseract（免费，离线，有语言包即可）

使用方法：
    from utils.ocr_helper import recognize_text, check_ocr_status

    # 识别图片中的文字
    result = recognize_text('screenshot.png')
    if result.success:
        print(f"文字: {result.text}")
        print(f"置信度: {result.confidence:.2%}")
    else:
        print(f"识别失败: {result.error}")

    # 截图并立即识别（Playwright）
    page.screenshot(path='temp.png')
    result = recognize_text('temp.png')
"""

import sys
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from utils.evolution.decorator import evolution_monitor

# OCR 引擎路径 - 优先加载
_OCR_ENGINE_PATH = r'C:\Users\Eddie\lobsterai\project\.learnings\tools\current\ocr_engine'
if _OCR_ENGINE_PATH not in sys.path:
    sys.path.insert(0, _OCR_ENGINE_PATH)

# 测试框架路径
sys.path.insert(0, r'C:\11_UITest')

# 加载配置
def _load_ocr_config():
    """从 config.yaml 加载 OCR 配置"""
    try:
        import yaml
        config_path = Path(r'C:\11_UITest\config\config.yaml')
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('ocr', {})
    except Exception:
        pass
    return {}

_OCR_CONFIG = _load_ocr_config()

# 优先使用新版 OCROptimizer（支持多引擎 fallback）
# 注意：ocr_engine 没有 __init__.py，需要直接导入 engine.py
_OCR_ENGINE = None
_OCR_PROCESSOR_AVAILABLE = False

try:
    from engine import OCROptimizer, OCREngineResult
    _OCR_ENGINE = 'optimizer'
except ImportError:
    pass

# 备用旧版 OCRProcessor（recognition.py 有 __all__ 或可独立导入）
try:
    from recognition import OCRProcessor, OCRResult as OCRProcessorResult
    _OCR_PROCESSOR_AVAILABLE = True
except ImportError:
    pass


@dataclass
class OCRTextResult:
    """统一的 OCR 结果格式"""
    success: bool
    text: str
    confidence: float  # 0.0 - 1.0
    engine: str  # 'baidu', 'local', 'tencent', 'processor'
    error: Optional[str] = None


def _convert_optimizer_result(result: 'OCREngineResult') -> OCRTextResult:
    """转换 OCROptimizer 结果为统一格式"""
    return OCRTextResult(
        success=result.success,
        text=result.text,
        confidence=result.confidence,
        engine=result.engine,
        error=result.error
    )


def _convert_processor_result(result: 'OCRProcessorResult') -> OCRTextResult:
    """转换 OCRProcessor 结果为统一格式"""
    return OCRTextResult(
        success=result.success,
        text=result.text,
        confidence=result.confidence,
        engine=result.provider,
        error=result.error
    )


@evolution_monitor("ocr_helper.recognize_text")
def recognize_text(
    image_path: str,
    prefer: str = None,
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None
) -> OCRTextResult:
    """
    识别图片中的文字（自动选择最优引擎）

    Args:
        image_path: 图片路径
        prefer: 偏好引擎 'baidu', 'local', 'auto'（默认从 config.yaml 读取）
        api_key: 百度 API Key（可选，默认从 config.yaml 读取）
        secret_key: 百度 Secret Key（可选，默认从 config.yaml 读取）

    Returns:
        OCRTextResult: 识别结果
    """
    if not os.path.exists(image_path):
        return OCRTextResult(
            success=False,
            text="",
            confidence=0.0,
            engine='none',
            error=f"图片文件不存在: {image_path}"
        )

    # 从 config 读取默认值
    if prefer is None:
        prefer = _OCR_CONFIG.get('prefer', 'baidu')
    if api_key is None:
        api_key = _OCR_CONFIG.get('baidu', {}).get('api_key', '')
    if secret_key is None:
        secret_key = _OCR_CONFIG.get('baidu', {}).get('secret_key', '')

    # 优先使用新版 OCROptimizer
    if _OCR_ENGINE == 'optimizer':
        optimizer = OCROptimizer(prefer=prefer)

        # 如果传入了 API Key，设置到 baidu 引擎
        if api_key and secret_key:
            optimizer.baidu.api_key = api_key
            optimizer.baidu.secret_key = secret_key
            optimizer.baidu.available = True
            if 'baidu' not in optimizer.available_engines:
                optimizer.available_engines.insert(0, 'baidu')

        result = optimizer.recognize(image_path)
        return _convert_optimizer_result(result)

    # 备用旧版 OCRProcessor
    if _OCR_PROCESSOR_AVAILABLE:
        processor = OCRProcessor(
            provider='baidu',
            api_key=api_key,
            secret_key=secret_key
        )
        result = processor.recognize(image_path=image_path)
        return _convert_processor_result(result)

    return OCRTextResult(
        success=False,
        text="",
        confidence=0.0,
        engine='none',
        error="没有可用的 OCR 引擎，请检查安装"
    )


def recognize_text_quick(image_path: str) -> OCRTextResult:
    """
    快速识别（使用本地优先策略）
    """
    return recognize_text(image_path, prefer='local')


def check_ocr_status() -> dict:
    """
    检查 OCR 引擎状态

    Returns:
        dict: 各引擎的可用状态
    """
    status = {
        'ocr_engine': _OCR_ENGINE,
        'ocr_processor': _OCR_PROCESSOR_AVAILABLE,
        'config': {
            'prefer': _OCR_CONFIG.get('prefer', 'baidu'),
            'baidu_configured': bool(_OCR_CONFIG.get('baidu', {}).get('api_key'))
        },
        'engines': {}
    }

    if _OCR_ENGINE == 'optimizer':
        optimizer = OCROptimizer()
        for name in ['local', 'baidu', 'tencent']:
            engine = getattr(optimizer, name, None)
            if engine:
                status['engines'][name] = {
                    'available': engine.available,
                    'error': None if engine.available else '未配置'
                }

    return status


# 便捷函数：识别并打印结果
def recognize_and_print(image_path: str, prefer: str = None) -> OCRTextResult:
    """识别图片并打印结果"""
    print(f"\n{'='*60}")
    print(f"OCR 识别: {image_path}")
    print(f"{'='*60}")

    result = recognize_text(image_path, prefer=prefer)

    if result.success:
        print(f"[OK] 识别成功")
        print(f"     引擎: {result.engine}")
        print(f"     置信度: {result.confidence:.2%}")
        print(f"     文字:")
        for line in result.text.split('\n'):
            if line.strip():
                print(f"      {line}")
    else:
        print(f"[FAIL] 识别失败")
        print(f"     引擎: {result.engine}")
        print(f"     错误: {result.error}")

    print(f"{'='*60}\n")
    return result


if __name__ == '__main__':
    import sys

    print("=" * 60)
    print("OCR 文字识别辅助工具")
    print("=" * 60)

    # 检查状态
    status = check_ocr_status()
    print(f"\nOCR 引擎状态:")
    print(f"  OCROptimizer: {'OK' if status['ocr_engine'] else 'MISSING'}")
    print(f"  OCRProcessor: {'OK' if status['ocr_processor'] else 'MISSING'}")
    print(f"  配置偏好: {status['config']['prefer']}")
    print(f"  百度API已配置: {'是' if status['config']['baidu_configured'] else '否'}")

    if status['engines']:
        print(f"\n  各引擎:")
        for name, info in status['engines'].items():
            icon = "OK" if info['available'] else "FAIL"
            print(f"    [{icon}] {name}: {info['error'] or '就绪'}")

    print(f"\n使用方法:")
    print(f"  from utils.ocr_helper import recognize_text")
    print(f"  result = recognize_text('screenshot.png')")
    print(f"  print(result.text)")

    # 如果有参数，执行快速识别
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if os.path.exists(image_path):
            recognize_and_print(image_path)
        else:
            print(f"\n文件不存在: {image_path}")

    print("=" * 60)