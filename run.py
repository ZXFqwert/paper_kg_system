#!/usr/bin/env python3
"""
论文知识图谱系统启动脚本
"""

import os
import sys
import subprocess

def check_requirements():
    """检查依赖是否已安装"""
    try:
        import flask
        import feedparser
        import aiohttp
        import tiktoken
        print("✓ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        return False

def install_requirements():
    """安装依赖"""
    print("正在安装依赖...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✓ 依赖安装完成")
        return True
    except subprocess.CalledProcessError:
        print("✗ 依赖安装失败")
        return False

def create_directories():
    """创建必要的目录"""
    directories = [
        'data',
        'data/papers',
        'data/graph',
        'static',
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✓ 目录结构创建完成")

def main():
    print("="*50)
    print("论文知识图谱系统")
    print("="*50)
    
    # 检查依赖
    if not check_requirements():
        print("\n是否自动安装依赖? (y/n): ", end="")
        choice = input().strip().lower()
        if choice == 'y':
            if not install_requirements():
                print("安装失败，请手动执行: pip install -r requirements.txt")
                return
        else:
            print("请手动安装依赖: pip install -r requirements.txt")
            return
    
    # 创建目录
    create_directories()
    
    # 启动应用
    print("\n启动应用...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务\n")
    
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")

if __name__ == "__main__":
    main() 