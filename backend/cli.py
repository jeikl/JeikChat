"""
JeikChat CLI 命令行工具
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

# 将 backend 目录添加到 Python 路径
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

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


def install_dependencies():
    """安装后端依赖"""
    print_header("正在安装后端依赖...")
    
    pyproject = BACKEND_DIR / "pyproject.toml"
    if not pyproject.exists():
        print(f"{YELLOW}未找到 pyproject.toml{RESET}")
        return 1
    
    cmd = f'"{sys.executable}" -m pip install -e .'
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR), shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{GREEN}依赖安装成功!{RESET}")
        return 0
    else:
        print(f"{YELLOW}安装失败: {result.stderr}{RESET}")
        return result.returncode


def start_backend(test_mode: bool = False, host: str = "0.0.0.0", port: int = 8000):
    """启动后端"""
    mode_str = "测试模式" if test_mode else "正常模式"
    print(f"\n{BLUE}启动后端 ({mode_str}) - {host}:{port}{RESET}")
    
    env = os.environ.copy()
    if test_mode:
        env["AICHAT_TEST_MODE"] = "1"
    
    # 支持双栈：如果指定 :: 或 0.0.0.0，都使用双栈模式
    if host in ["::", "0.0.0.0"]:
        import platform
        if platform.system() == "Windows":
            cmd = f'"{sys.executable}" -m uvicorn main:app --host 0.0.0.0 --port {port} --reload'
        else:
            cmd = f'"{sys.executable}" -m uvicorn main:app --host :: --port {port} --reload'
    else:
        cmd = f'"{sys.executable}" -m uvicorn main:app --host {host} --port {port} --reload'
    
    # 直接运行并显示输出
    process = subprocess.Popen(
        cmd,
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=None,  # 直接输出到终端
        stderr=None,
        shell=True
    )
    
    return process


def start_frontend(host: str = "::", port: int = 5173):
    """启动前端"""
    vite_host = "::" if host in ["0.0.0.0", "::"] else host
    print(f"\n{BLUE}启动前端 - {vite_host}:{port}{RESET}")
    
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("首次运行，安装前端依赖...")
        result = subprocess.run("npm install", cwd=str(FRONTEND_DIR), shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"{YELLOW}npm install 失败: {result.stderr}{RESET}")
            return None
    
    # 设置前端主机和端口
    env = os.environ.copy()
    env["HOST"] = vite_host
    env["PORT"] = str(port)
    
    # 直接运行并显示输出
    process = subprocess.Popen(
        f"npm run dev -- --host {vite_host} --port {port}",
        cwd=str(FRONTEND_DIR),
        env=env,
        stdout=None,
        stderr=None,
        shell=True
    )
    
    return process


def run_back_test(host: str = "0.0.0.0", port: int = 8000):
    """运行后端测试数据接口"""
    print_header("🔧 启动后端测试数据服务")
    
    proc = start_backend(test_mode=True, host=host, port=port)
    
    time.sleep(5)
    
    # 尝试打开多个地址
    addresses = [
        f"http://localhost:{port}/docs",
        f"http://127.0.0.1:{port}/docs",
        f"http://[::1]:{port}/docs",  # IPv6 localhost
        f"http://{host}:{port}/docs" if host != "0.0.0.0" else None
    ]
    
    for addr in addresses:
        if addr:
            open_browser(addr)
    
    print(f"\n{GREEN}✅ 后端测试服务已启动!{RESET}")
    print(f"API 文档地址:")
    print(f"  - {BLUE}http://localhost:{port}/docs{RESET}")
    print(f"  - {BLUE}http://127.0.0.1:{port}/docs{RESET}")
    print(f"  - {BLUE}http://[::1]:{port}/docs{RESET} (IPv6)")
    if host != "0.0.0.0":
        print(f"  - {BLUE}http://{host}:{port}/docs{RESET}")
    print(f"\n请手动打开浏览器访问以上地址")
    print(f"按 {YELLOW}Ctrl+C{RESET} 停止服务\n")
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}正在停止服务...{RESET}")
        proc.terminate()
        proc.wait()


def run_back(host: str = "0.0.0.0", port: int = 8000):
    """启动后端正常模式"""
    print_header("🚀 启动后端服务")
    
    proc = start_backend(test_mode=False, host=host, port=port)
    
    time.sleep(5)
    
    # 尝试打开多个地址
    addresses = [
        f"http://localhost:{port}/docs",
        f"http://127.0.0.1:{port}/docs",
        f"http://[::1]:{port}/docs",  # IPv6 localhost
        f"http://{host}:{port}/docs" if host != "0.0.0.0" else None
    ]
    
    for addr in addresses:
        if addr:
            open_browser(addr)
    
    print(f"\n{GREEN}✅ 后端服务已启动!{RESET}")
    print(f"API 文档地址:")
    print(f"  - {BLUE}http://localhost:{port}/docs{RESET}")
    print(f"  - {BLUE}http://127.0.0.1:{port}/docs{RESET}")
    print(f"  - {BLUE}http://[::1]:{port}/docs{RESET} (IPv6)")
    if host != "0.0.0.0":
        print(f"  - {BLUE}http://{host}:{port}/docs{RESET}")
    print(f"\n请手动打开浏览器访问以上地址")
    print(f"按 {YELLOW}Ctrl+C{RESET} 停止服务\n")
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}正在停止服务...{RESET}")
        proc.terminate()
        proc.wait()


def run_front(host: str = "localhost", port: int = 5173):
    """启动前端"""
    print_header("🎨 启动前端服务")
    
    proc = start_frontend(host=host, port=port)
    
    if proc is None:
        print(f"{YELLOW}前端启动失败{RESET}")
        return
    
    time.sleep(8)
    
    # 尝试打开多个地址
    addresses = [
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}",
        f"http://[::1]:{port}",  # IPv6 localhost
        f"http://{host}:{port}" if host != "localhost" else None
    ]
    
    for addr in addresses:
        if addr:
            open_browser(addr)
    
    print(f"\n{GREEN}✅ 前端服务已启动!{RESET}")
    print(f"前端地址:")
    print(f"  - {BLUE}http://localhost:{port}{RESET}")
    print(f"  - {BLUE}http://127.0.0.1:{port}{RESET}")
    print(f"  - {BLUE}http://[::1]:{port}{RESET} (IPv6)")
    if host != "localhost":
        print(f"  - {BLUE}http://{host}:{port}{RESET}")
    print(f"\n请手动打开浏览器访问以上地址")
    print(f"按 {YELLOW}Ctrl+C{RESET} 停止服务\n")
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}正在停止服务...{RESET}")
        proc.terminate()
        proc.wait()


def run_all(test_mode: bool = False, backend_host: str = "0.0.0.0", backend_port: int = 8000, frontend_host: str = "localhost", frontend_port: int = 5173):
    """启动全栈"""
    mode_str = "测试模式" if test_mode else "正常模式"
    print_header(f"🌐 启动全栈服务 ({mode_str})")
    
    backend_proc = start_backend(test_mode=test_mode, host=backend_host, port=backend_port)
    time.sleep(5)
    
    frontend_proc = start_frontend(host=frontend_host, port=frontend_port)
    if frontend_proc is None:
        print(f"{YELLOW}前端启动失败{RESET}")
        backend_proc.terminate()
        backend_proc.wait()
        return
    
    time.sleep(8)
    
    # 只打开一个浏览器窗口
    open_browser(f"http://localhost:{frontend_port}")
    
    print(f"\n{GREEN}✅ 全栈服务已启动!{RESET}")
    print(f"前端地址: {BLUE}http://localhost:{frontend_port}{RESET}")
    print(f"后端地址: {BLUE}http://localhost:{backend_port}/docs{RESET}")
    print(f"\n按 {YELLOW}Ctrl+C{RESET} 停止\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}停止服务...{RESET}")
        frontend_proc.terminate()
        backend_proc.terminate()
        print(f"{GREEN}已停止{RESET}")


def run_all_simple(test_mode: bool = False):
    """简化版全栈启动 - 使用 StartConfig 配置"""
    from init import StartConfig
    
    config = StartConfig.from_env()
    config.print_config()
    
    mode_str = "测试模式" if test_mode else "正常模式"
    print_header(f"🌐 启动全栈服务 ({mode_str})")
    
    backend_proc = start_backend(test_mode=test_mode, host=config.backend_host, port=config.backend_port)
    time.sleep(5)
    
    frontend_proc = start_frontend(host=config.frontend_host, port=config.frontend_port)
    if frontend_proc is None:
        print(f"{YELLOW}前端启动失败{RESET}")
        backend_proc.terminate()
        backend_proc.wait()
        return
    
    time.sleep(8)
    
    # 打开前端页面
    open_browser(f"http://localhost:{config.frontend_port}")
    
    print(f"\n{GREEN}✅ 全栈服务已启动!{RESET}")
    print(f"前端地址: {BLUE}http://localhost:{config.frontend_port}{RESET}")
    print(f"后端地址: {BLUE}http://localhost:{config.backend_port}/docs{RESET}")
    print(f"API 文档: {BLUE}{config.api_docs_url}{RESET}")
    print(f"\n按 {YELLOW}Ctrl+C{RESET} 停止\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}停止服务...{RESET}")
        frontend_proc.terminate()
        backend_proc.terminate()
        print(f"{GREEN}已停止{RESET}")


def main():
    parser = argparse.ArgumentParser(
        description=f"{GREEN}JeikChat CLI{RESET}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{GREEN}使用示例:{RESET}
  {YELLOW}jeikchat run a{RESET}                        简化启动全栈 (推荐)
  {YELLOW}jeikchat run back -t{RESET}                   后端测试模式
  {YELLOW}jeikchat run back --host :: --port 8080{RESET}        后端IPv6模式，端口8080
  {YELLOW}jeikchat run front --host 192.168.1.100 --port 3000{RESET} 前端指定IP和端口
  {YELLOW}jeikchat run all -t{RESET}                    全栈测试模式
  {YELLOW}jeikchat run all --host :: --port 9000{RESET}         全栈IPv6模式
  {YELLOW}jeikchat install{RESET}                       安装依赖
        """
    )
    
    parser.add_argument("action", nargs="?", help="要执行的操作")
    parser.add_argument("target", nargs="?", help="目标 (a/back/front/all)")
    parser.add_argument("-t", "--test", action="store_true", help="测试模式")
    parser.add_argument("--host", default=None, help="指定主机地址 (如: 0.0.0.0, ::, 192.168.1.100)")
    parser.add_argument("--port", type=int, default=None, help="指定前端端口号")
    parser.add_argument("--backend-port", type=int, default=None, help="指定后端端口号")
    parser.add_argument("--frontend-port", type=int, default=None, help="指定前端端口号")
    parser.add_argument("--mode", choices=["dev", "local"], default="dev", help="环境模式 (dev/local)")
    
    args = parser.parse_args()
    
    # 设置默认值
    backend_host = args.host if args.host else "0.0.0.0"
    backend_port = args.backend_port if args.backend_port else (args.port if args.port else 8000)
    frontend_host = args.host if args.host else "localhost"
    frontend_port = args.frontend_port if args.frontend_port else (args.port if args.port else 5173)
    
    # 设置环境模式
    os.environ["AICHAT_ENVIRONMENT"] = args.mode
    
    if args.action == "run" and args.target:
        target = args.target.lower()
        if target in ["a", "all"]:  # 支持简化的 'a' 命令
            if target == "a":
                run_all_simple(test_mode=args.test)
            else:
                run_all(
                    test_mode=args.test,
                    backend_host=backend_host,
                    backend_port=backend_port,
                    frontend_host=frontend_host,
                    frontend_port=frontend_port
                )
        elif target == "back":
            if args.test:
                run_back_test(host=backend_host, port=backend_port)
            else:
                run_back(host=backend_host, port=backend_port)
        elif target == "front":
            run_front(host=frontend_host, port=frontend_port)
        else:
            print(f"{YELLOW}未知目标: {target}{RESET}")
    elif args.action == "install":
        install_dependencies()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
