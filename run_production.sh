#!/bin/bash

# 生产环境启动脚本
# Production startup script for XueXinWang Archive Management System

# 切换到应用目录
cd "$(dirname "$0")"

# 确保Gunicorn已安装
if ! command -v gunicorn &> /dev/null; then
    echo "安装Gunicorn..."
    pip install gunicorn
fi

# 使用Gunicorn启动应用
echo "使用Gunicorn启动生产服务器..."
echo "配置文件: gunicorn_config.py"

# 启动Gunicorn
exec gunicorn -c gunicorn_config.py app:app