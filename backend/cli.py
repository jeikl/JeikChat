"""
JeikChat CLI 命令行工具
简化版 - 直接启动服务
"""
import argparse
import subprocess
import sys
import os
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str):
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{GREEN}{text}{RESET}")
    print(f"{BLUE}{'='*50}{RESET}\n")


def open_browser(url: str):
    """用 Windows start 命令打开浏览器"""
    try:
        os.system(f'start "" "{url}"')
    except:
        pass


def start_backend(test_mode: bool = False, host: str = "localhost", port: int = 8000):
    """启动后端"""
    mode_str = "测试模式" if test_mode else "正常模式"
    print(f"\n{BLUE}启动后端 ({mode_str}) - http://{host}:{port}{RESET}")
    
    env = os.environ.copy()
    if test_mode:
        env["AICHAT_TEST_MODE"] = "1"
    
    cmd = f'"{sys.executable}" -m uvicorn app.main:app --host {host} --port {port} --reload'
    
    process = subprocess.Popen(
        cmd,
        cwd=str(BACKEND_DIR),
        env=env,
        shell=True
    )
    
    return process


def start_frontend(port: int = 5173):
    """启动前端"""
    print(f"\n{BLUE}启动前端 - http://localhost:{port}{RESET}")
    
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("首次运行，安装前端依赖...")
        result = subprocess.run("npm install", cwd=str(FRONTEND_DIR), shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"{YELLOW}npm install 失败: {result.stderr.decode() if result.stderr else ''}{RESET}")
            return None
    
    cmd = f'npm run dev -- --host 0.0.0.0 --port {port}'
    process = subprocess.Popen(
        cmd,
        cwd=str(FRONTEND_DIR),
        shell=True
    )
    
    return process


def run_backend(test_mode: bool = False, host: str = "0.0.0.0", port: int = 8000):
    """启动后端服务"""
    print_header("� 启动后端服务")
    
    proc = start_backend(test_mode=test_mode, host=host, port=port)
    
    if proc is None:
        print(f"{YELLOW}后端启动失败{RESET}")
        return
    
    time.sleep(3)
    
    print(f"\n{GREEN}✅ 后端已启动!{RESET}")
    print(f"API 文档: {BLUE}http://localhost:{port}/docs{RESET}")
    print(f"按 {YELLOW}Ctrl+C{RESET} 停止\n")
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}停止服务...{RESET}")
        proc.terminate()
        proc.wait()


def run_frontend(port: int = 5173):
    """启动前端服务"""
    print_header("🎨 启动前端服务")
    
    proc = start_frontend(port=port)
    
    if proc is None:
        print(f"{YELLOW}前端启动失败{RESET}")
        return
    
    time.sleep(5)
    open_browser(f"http://localhost:{port}")
    
    print(f"\n{GREEN}✅ 前端已启动!{RESET}")
    print(f"前端地址: {BLUE}http://localhost:{port}{RESET}")
    print(f"按 {YELLOW}Ctrl+C{RESET} 停止\n")
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}停止服务...{RESET}")
        proc.terminate()
        proc.wait()


def run_all(test_mode: bool = False, backend_port: int = 8000, frontend_port: int = 5173):
    """启动全栈服务"""
    print_header("🌐 启动全栈服务")
    
    backend_proc = start_backend(test_mode=test_mode, port=backend_port)
    time.sleep(3)
    
    frontend_proc = start_frontend(port=frontend_port)
    if frontend_proc is None:
        print(f"{YELLOW}前端启动失败{RESET}")
        backend_proc.terminate()
        backend_proc.wait()
        return
    
    time.sleep(5)
    open_browser(f"http://localhost:{frontend_port}")
    
    print(f"\n{GREEN}✅ 全栈已启动!{RESET}")
    print(f"前端: {BLUE}http://localhost:{frontend_port}{RESET}")
    print(f"后端: {BLUE}http://localhost:{backend_port}/docs{RESET}")
    print(f"按 {YELLOW}Ctrl+C{RESET} 停止\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}停止服务...{RESET}")
        frontend_proc.terminate()
        backend_proc.terminate()
        print(f"{GREEN}已停止{RESET}")


def main():
    parser = argparse.ArgumentParser(description=f"{GREEN}JeikChat CLI{RESET}")
    
    parser.add_argument("action", nargs="?", help="操作: back/front/all")
    parser.add_argument("-t", "--test", action="store_true", help="测试模式")
    parser.add_argument("--port", type=int, default=8000, help="后端端口 (默认 8000)")
    parser.add_argument("--front-port", type=int, default=5173, help="前端端口 (默认 5173)")
    
    args = parser.parse_args()
    
    action = args.action
    
    if action in ["back", "backend"]:
        run_backend(test_mode=args.test, port=args.port)
    elif action in ["front", "frontend"]:
        run_frontend(port=args.front_port)
    elif action in ["all", "a"]:
        run_all(test_mode=args.test, backend_port=args.port, frontend_port=args.front_port)
    else:
        print(f"""
{GREEN}JeikChat CLI{RESET}

使用方式:
  {YELLOW}jeikchat back{RESET}           启动后端 (默认端口 8000)
  {YELLOW}jeikchat back -t{RESET}        后端测试模式
  {YELLOW}jeikchat back --port 8080{RESET} 后端指定端口
  {YELLOW}jeikchat front{RESET}          启动前端 (默认端口 5173)
  {YELLOW}jeikchat all{RESET}             启动全栈
  {YELLOW}jeikchat a{RESET}               启动全栈 (简化)
        """)


if __name__ == "__main__":
    main()
