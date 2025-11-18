@echo off
REM 云服务器快速修复脚本 (Windows版本)
REM 用于在云服务器上快速应用日志配置修复

echo ==========================================
echo AI幻想助手后端 - 云服务器日志修复脚本
echo ==========================================

REM 检查当前目录
if not exist "run.py" (
    echo ❌ 错误: 请在项目根目录运行此脚本
    pause
    exit /b 1
)

echo ✅ 当前目录正确

REM 设置环境变量
echo 📝 设置环境变量...
set PYTHONUNBUFFERED=1
set FLASK_ENV=production

REM 检查Python版本
echo 🐍 检查Python版本...
python --version

REM 检查关键包
echo 📦 检查关键包...
python -c "import flask, flask_socketio, zai, httpx; print('✅ 所有关键包已安装')"

REM 运行环境检测
echo 🔍 运行环境检测...
python check_environment.py

REM 运行流式响应测试
echo 🧪 运行流式响应测试...
python test_stream.py

echo.
echo ==========================================
echo 修复完成！现在可以启动应用：
echo python run.py
echo ==========================================

REM 提供启动选项
set /p choice="是否现在启动应用？(y/n): "
if /i "%choice%"=="y" (
    echo 🚀 启动应用...
    python run.py
)

pause