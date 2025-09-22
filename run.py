#!/usr/bin/env python
"""
学籍信息管理系统 - 启动脚本
"""
import sys
import os

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, Config

if __name__ == '__main__':
    print("=" * 50)
    print("学籍信息管理系统")
    print("=" * 50)
    print(f"访问地址: http://{Config.HOST}:{Config.PORT}")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)

    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )