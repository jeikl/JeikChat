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

echo "📂 .venv/bin 目录内容:"
ls -la /backend/.venv/bin/ | head -20

echo "📂 config 目录内容:"
ls -la /backend/config/

# 检查 uvicorn 的 shebang
echo "🔍 检查 uvicorn 的 shebang:"
head -1 /backend/.venv/bin/uvicorn

# 检查 python 是否存在
echo "🔍 检查 python:"
ls -la /backend/.venv/bin/python* 2>/dev/null || echo "❌ python 不存在"
which python3

# 尝试用 python -m 启动
echo "🚀 启动 uvicorn (使用 python -m)..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
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
