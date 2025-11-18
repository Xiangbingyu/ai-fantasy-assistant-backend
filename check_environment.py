#!/usr/bin/env python3
"""
环境检测脚本
用于检测本地和云服务器环境的差异
"""

import sys
import os
import platform
import socket
import subprocess
from datetime import datetime

def check_environment():
    """检查环境信息"""
    print("=" * 60)
    print("环境检测报告")
    print("=" * 60)
    
    # 基本系统信息
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print(f"架构: {platform.machine()}")
    print(f"主机名: {socket.gethostname()}")
    
    # 网络信息
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"本地IP: {local_ip}")
    except:
        print("无法获取本地IP")
    
    # 环境变量
    print(f"\n关键环境变量:")
    env_vars = [
        'PYTHONUNBUFFERED',
        'FLASK_ENV',
        'FLASK_DEBUG',
        'DATABASE_URL',
        'ZHIPU_API_KEY',
        'PATH'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if var in ['ZHIPU_API_KEY']:
                print(f"  {var}: {'*' * 10}...{value[-4:]}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: 未设置")
    
    # Python包版本
    print(f"\n关键Python包版本:")
    packages = [
        'flask',
        'flask-socketio',
        'zai',
        'httpx',
        'sqlalchemy'
    ]
    
    for package in packages:
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        print(f"  {package}: {line.split(':')[1].strip()}")
                        break
            else:
                print(f"  {package}: 未安装")
        except:
            print(f"  {package}: 无法获取版本")
    
    # 网络连接测试
    print(f"\n网络连接测试:")
    test_urls = [
        'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        'https://www.baidu.com'
    ]
    
    for url in test_urls:
        try:
            import urllib.request
            response = urllib.request.urlopen(url, timeout=5)
            print(f"  {url}: ✅ 连接成功 (状态码: {response.getcode()})")
        except Exception as e:
            print(f"  {url}: ❌ 连接失败 ({str(e)})")
    
    # 当前工作目录和权限
    print(f"\n文件系统信息:")
    print(f"  当前工作目录: {os.getcwd()}")
    print(f"  可写性测试: ", end="")
    try:
        test_file = "write_test.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ 可写")
    except:
        print("❌ 不可写")
    
    # 进程信息
    print(f"\n进程信息:")
    print(f"  进程ID: {os.getpid()}")
    print(f"  父进程ID: {os.getppid()}")
    print(f"  用户ID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
    
    print(f"\n检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    check_environment()