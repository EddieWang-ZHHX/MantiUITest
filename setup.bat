@echo off
echo ========================================
echo UI 自动化测试框架 - 安装脚本
echo ========================================
echo.

echo [1/3] 安装 Python 依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误：依赖安装失败！
    pause
    exit /b 1
)

echo.
echo [2/3] 安装 Playwright 浏览器...
playwright install
if errorlevel 1 (
    echo 错误：Playwright 安装失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 安装 Playwright 系统依赖...
playwright install-deps
if errorlevel 1 (
    echo 警告：系统依赖安装可能失败，可以忽略
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 运行测试命令：
echo   pytest                    - 运行所有测试
echo   pytest tests/test_example.py - 运行示例测试
echo   pytest -m smoke           - 运行冒烟测试
echo.
pause
