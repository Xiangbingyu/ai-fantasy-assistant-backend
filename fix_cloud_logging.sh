#!/bin/bash
# 云服务器快速修复脚本
# 用于在云服务器上快速应用日志配置修复

echo "=========================================="
echo "AI幻想助手后端 - 云服务器日志修复脚本"
echo "=========================================="

# 检查当前目录
if [ ! -f "run.py" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

echo "✅ 当前目录正确"

# 设置环境变量
echo "📝 设置环境变量..."
export PYTHONUNBUFFERED=1
export FLASK_ENV=production

# 检查Python版本
echo "🐍 检查Python版本..."
python3 --version

# 检查关键包
echo "📦 检查关键包..."
python3 -c "import flask, flask_socketio, zai, httpx; print('✅ 所有关键包已安装')"

# 运行环境检测
echo "🔍 运行环境检测..."
python3 check_environment.py

# 运行流式响应测试
echo "🧪 运行流式响应测试..."
python3 test_stream.py

echo ""
echo "=========================================="
echo "修复完成！现在可以启动应用："
echo "python3 run.py"
echo "=========================================="

# 提供启动选项
read -p "是否现在启动应用？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 启动应用..."
    python3 run.py
fi