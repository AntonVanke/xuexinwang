#!/bin/bash

# 临时修复脚本 - 解决host配置问题
# Fixed startup script for XueXinWang

cd "$(dirname "$0")"

# 设置默认值
PORT=5000
HOST="0.0.0.0"

# 尝试从config.json读取配置
if [ -f "config.json" ]; then
    echo "读取配置文件..."

    # 使用Python解析JSON（最可靠的方法）
    if command -v python3 &> /dev/null; then
        PORT=$(python3 -c "import json; data=json.load(open('config.json')); print(data.get('port', 5000))" 2>/dev/null || echo "5000")
        HOST=$(python3 -c "import json; data=json.load(open('config.json')); print(data.get('host', '0.0.0.0'))" 2>/dev/null || echo "0.0.0.0")
    elif command -v python &> /dev/null; then
        PORT=$(python -c "import json; data=json.load(open('config.json')); print(data.get('port', 5000))" 2>/dev/null || echo "5000")
        HOST=$(python -c "import json; data=json.load(open('config.json')); print(data.get('host', '0.0.0.0'))" 2>/dev/null || echo "0.0.0.0")
    fi
fi

echo "配置: HOST=$HOST PORT=$PORT"

# 检查是源码还是编译版本
if [ -f "app.py" ]; then
    echo "检测到源码版本"

    # 检查并安装Gunicorn
    if ! command -v gunicorn &> /dev/null; then
        echo "安装Gunicorn..."
        pip install gunicorn || pip3 install gunicorn
    fi

    # 如果有gunicorn_config.py，使用它
    if [ -f "gunicorn_config.py" ]; then
        echo "使用Gunicorn配置文件启动..."
        exec gunicorn -c gunicorn_config.py app:app
    else
        # 直接使用Gunicorn命令行参数
        echo "使用Gunicorn启动（命令行参数）..."
        exec gunicorn --bind "$HOST:$PORT" --workers 4 --timeout 30 app:app
    fi
elif [ -f "xuexinwang" ]; then
    echo "检测到编译版本"
    echo "启动命令: ./xuexinwang --host \"$HOST\" --port $PORT"
    exec ./xuexinwang --host "$HOST" --port $PORT
else
    echo "错误: 找不到app.py或xuexinwang可执行文件"
    exit 1
fi