"""日志工具"""
from loguru import logger
from pathlib import Path
import sys


def setup_logger(log_file: str = "logs/test.log", level: str = "INFO"):
    """设置日志"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        log_path,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    return logger


# 初始化日志
logger = setup_logger()
