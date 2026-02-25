#!/usr/bin/env python3
"""
JeikChat 测试模式调试启动脚本
支持在调试模式下启动测试模式，便于调试API接口
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# 添加后端目录到Python路径
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

def start_backend_debug(test_mode: bool = True, host: str = "::", port: int = 8000):
    """启动后端调试模式"""
    print("🚀 启动后端调试模式...")
    
    # 设置环境变量
    env = os.environ.copy()
    if test_mode:
        env["AICHAT_TEST_MODE"] = "1"
    
    # 启用Python调试模式
    env["PYTHONPATH"] = str(BACKEND_DIR)
    
    # 启动命令 - 使用uvicorn的reload模式，便于调试
    cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", host, "--port", str(port),
        "--reload", "--reload-dir", str(BACKEND_DIR)
    ]
    
    print(f"后端启动命令: {' '.join(cmd)}")
    print(f"测试模式: {'开启' if test_mode else '关闭'}")
    print(f"监听地址: {host}:{port}")
    
    # 启动后端进程
    backend_proc = subprocess.Popen(
        cmd,
        cwd=str(BACKEND_DIR),
        env=env
    )
    
    return backend_proc

def start_frontend_debug(host: str = "::", port: int = 5173):
    """启动前端调试模式"""
    print("🎨 启动前端调试模式...")
    
    # 检查node_modules是否存在
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("首次运行，安装前端依赖...")
        result = subprocess.run("npm install", cwd=str(FRONTEND_DIR), shell=True)
        if result.returncode != 0:
            print("npm install 失败")
            return None
    
    # 设置环境变量
    env = os.environ.copy()
    env["HOST"] = host
    env["PORT"] = str(port)
    
    # 启动命令
    cmd = ["npm", "run", "dev", "--", "--host", host, "--port", str(port)]
    
    print(f"前端启动命令: {' '.join(cmd)}")
    print(f"监听地址: {host}:{port}")
    
    # 启动前端进程
    frontend_proc = subprocess.Popen(
        cmd,
        cwd=str(FRONTEND_DIR),
        env=env
    )
    
    return frontend_proc

def main():
    """主函数"""
    print("=" * 60)
    print("🔧 JeikChat 测试模式调试启动器")
    print("=" * 60)
    
    # 启动后端
    backend_proc = start_backend_debug(test_mode=True, host="::", port=8000)
    
    # 等待后端启动
    print("等待后端启动...")
    time.sleep(5)
    
    # 启动前端
    frontend_proc = start_frontend_debug(host="::", port=5173)
    
    print("\n" + "=" * 60)
    print("✅ 调试模式已启动!")
    print("=" * 60)
    print("\n访问地址:")
    print("  🌐 前端应用: http://localhost:5173")
    print("  📚 API文档: http://localhost:8000/docs")
    print("  🔍 测试接口: http://localhost:8000/api/chat/send")
    print("\n调试信息:")
    print("  • 后端运行在调试模式，支持热重载")
    print("  • 前端运行在开发模式，支持热重载")
    print("  • 所有API调用将使用测试数据")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        # 等待进程结束
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("服务已停止")

if __name__ == "__main__":
    main()