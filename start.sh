#!/bin/bash
set -e

echo "🚀 启动 JeikChat..."

# 启动后端服务（后台运行）
echo "📡 启动后端服务..."
cd /backend

# 设置 PYTHONPATH 以正确加载模块
export PYTHONPATH=/backend
echo "📋 PYTHONPATH: $PYTHONPATH"

# 调试信息
echo "📂 当前目录: $(pwd)"
echo "📂 目录内容:"
ls -la /backend/

uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ 后端服务启动失败"
    exit 1
fi

echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

# 启动 Nginx（前台运行）
echo "🌐 启动 Nginx..."
nginx -g 'daemon off;'
