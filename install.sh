#!/bin/bash

# 学信网档案管理系统安装脚本
# Installation script for XueXinWang Archive Management System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_PORT=5000
DEFAULT_HOST="127.0.0.1"
INSTALL_DIR="/opt/xuexinwang"
SERVICE_NAME="xuexinwang"
SERVICE_USER="xuexinwang"
GITHUB_REPO="AntonVanke/xuexinwang"  # 请替换为您的GitHub用户名

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_message "此脚本需要root权限运行。请使用 sudo 运行此脚本。" "$RED"
        exit 1
    fi
}

# Function to detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        print_message "无法检测操作系统版本" "$RED"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    local missing_deps=()

    for cmd in wget tar systemctl; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_message "缺少必要的依赖: ${missing_deps[*]}" "$RED"
        print_message "请先安装这些依赖。" "$YELLOW"
        exit 1
    fi
}

# Interactive configuration
configure_installation() {
    print_message "\n=== 学信网档案管理系统安装配置 ===" "$BLUE"

    # Port configuration
    read -p "请输入服务端口 (默认: $DEFAULT_PORT): " PORT
    PORT=${PORT:-$DEFAULT_PORT}

    # Validate port
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
        print_message "无效的端口号，使用默认端口 $DEFAULT_PORT" "$YELLOW"
        PORT=$DEFAULT_PORT
    fi

    # Check if port is already in use
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_message "端口 $PORT 已被占用" "$YELLOW"
        read -p "是否继续？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # External access configuration
    print_message "\n是否允许外部访问？" "$BLUE"
    print_message "  1) 仅本机访问 (127.0.0.1)" "$NC"
    print_message "  2) 允许局域网访问 (0.0.0.0)" "$NC"
    read -p "请选择 (1-2, 默认: 1): " ACCESS_CHOICE

    case $ACCESS_CHOICE in
        2)
            HOST="0.0.0.0"
            print_message "已设置为允许外部访问" "$GREEN"
            print_message "警告: 请确保已配置防火墙规则" "$YELLOW"
            ;;
        *)
            HOST=$DEFAULT_HOST
            print_message "已设置为仅本机访问" "$GREEN"
            ;;
    esac

    # Installation directory
    read -p "安装目录 (默认: $INSTALL_DIR): " CUSTOM_INSTALL_DIR
    INSTALL_DIR=${CUSTOM_INSTALL_DIR:-$INSTALL_DIR}

    # Auto-start configuration
    read -p "是否设置开机自启动？(y/n, 默认: y): " -n 1 -r AUTO_START
    echo
    AUTO_START=${AUTO_START:-y}

    # Display configuration summary
    print_message "\n=== 配置摘要 ===" "$BLUE"
    print_message "端口: $PORT" "$NC"
    print_message "监听地址: $HOST" "$NC"
    print_message "安装目录: $INSTALL_DIR" "$NC"
    print_message "开机自启: $([ "$AUTO_START" = "y" ] || [ "$AUTO_START" = "Y" ] && echo "是" || echo "否")" "$NC"

    read -p "确认以上配置？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message "安装已取消" "$YELLOW"
        exit 1
    fi
}

# Function to get latest release
get_latest_release() {
    print_message "\n正在获取最新版本..." "$BLUE"

    LATEST_RELEASE=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

    if [ -z "$LATEST_RELEASE" ]; then
        print_message "无法获取最新版本，将使用 v1.0.0" "$YELLOW"
        LATEST_RELEASE="v1.0.0"
    fi

    print_message "最新版本: $LATEST_RELEASE" "$GREEN"
    DOWNLOAD_URL="https://github.com/$GITHUB_REPO/releases/download/$LATEST_RELEASE/xuexinwang-linux-amd64.tar.gz"
}

# Function to download and extract
download_and_extract() {
    print_message "\n正在下载..." "$BLUE"

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd $TEMP_DIR

    # Download release
    if ! wget -q --show-progress "$DOWNLOAD_URL" -O xuexinwang.tar.gz; then
        print_message "下载失败" "$RED"
        rm -rf $TEMP_DIR
        exit 1
    fi

    print_message "正在解压..." "$BLUE"
    tar -xzf xuexinwang.tar.gz

    # Check if installation directory exists
    if [ -d "$INSTALL_DIR" ]; then
        print_message "安装目录已存在" "$YELLOW"
        read -p "是否覆盖安装？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Backup existing data
            if [ -f "$INSTALL_DIR/students.db" ]; then
                print_message "备份数据库..." "$BLUE"
                cp "$INSTALL_DIR/students.db" "$INSTALL_DIR/students.db.bak.$(date +%Y%m%d%H%M%S)"
            fi
            if [ -d "$INSTALL_DIR/uploads" ]; then
                print_message "备份上传文件..." "$BLUE"
                cp -r "$INSTALL_DIR/uploads" "$INSTALL_DIR/uploads.bak.$(date +%Y%m%d%H%M%S)"
            fi
            rm -rf "$INSTALL_DIR"
        else
            print_message "安装已取消" "$YELLOW"
            rm -rf $TEMP_DIR
            exit 1
        fi
    fi

    # Move to installation directory
    print_message "正在安装到 $INSTALL_DIR..." "$BLUE"
    mv xuexinwang "$INSTALL_DIR"

    # Restore backups if they exist
    if [ -f "$INSTALL_DIR.bak/students.db" ]; then
        print_message "恢复数据库..." "$BLUE"
        mv "$INSTALL_DIR.bak/students.db" "$INSTALL_DIR/students.db"
    fi
    if [ -d "$INSTALL_DIR.bak/uploads" ]; then
        print_message "恢复上传文件..." "$BLUE"
        mv "$INSTALL_DIR.bak/uploads" "$INSTALL_DIR/uploads"
    fi

    cd /
    rm -rf $TEMP_DIR
}

# Function to create system user
create_system_user() {
    if ! id "$SERVICE_USER" &>/dev/null; then
        print_message "创建系统用户 $SERVICE_USER..." "$BLUE"
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
    fi

    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/xuexinwang"
}

# Function to create config file
create_config() {
    print_message "创建配置文件..." "$BLUE"

    cat > "$INSTALL_DIR/config.json" << EOF
{
    "port": $PORT,
    "host": "$HOST",
    "debug": false
}
EOF

    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/config.json"
}

# Function to create wrapper script
create_wrapper_script() {
    print_message "创建启动脚本..." "$BLUE"

    cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash

# Load configuration
CONFIG_FILE="$(dirname "$0")/config.json"

if [ -f "$CONFIG_FILE" ]; then
    PORT=$(grep -o '"port":[^,}]*' "$CONFIG_FILE" | cut -d: -f2 | tr -d ' ')
    HOST=$(grep -o '"host":"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
else
    PORT=5000
    HOST="127.0.0.1"
fi

# Change to application directory
cd "$(dirname "$0")"

# Export Flask environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

# Start the application
exec ./xuexinwang --host "$HOST" --port "$PORT"
EOF

    chmod +x "$INSTALL_DIR/start.sh"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/start.sh"
}

# Function to create systemd service
create_systemd_service() {
    if [[ ! "$AUTO_START" =~ ^[Yy]$ ]]; then
        return
    fi

    print_message "创建systemd服务..." "$BLUE"

    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=XueXinWang Archive Management System
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload

    if [[ "$AUTO_START" =~ ^[Yy]$ ]]; then
        systemctl enable "$SERVICE_NAME.service"
        print_message "已设置开机自启动" "$GREEN"
    fi
}

# Function to configure firewall
configure_firewall() {
    if [ "$HOST" != "127.0.0.1" ]; then
        print_message "\n配置防火墙..." "$BLUE"

        # Check for ufw
        if command -v ufw &> /dev/null; then
            read -p "是否添加防火墙规则允许端口 $PORT？(y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ufw allow $PORT/tcp
                print_message "已添加防火墙规则" "$GREEN"
            fi
        fi

        # Check for firewalld
        if command -v firewall-cmd &> /dev/null; then
            read -p "是否添加防火墙规则允许端口 $PORT？(y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                firewall-cmd --permanent --add-port=$PORT/tcp
                firewall-cmd --reload
                print_message "已添加防火墙规则" "$GREEN"
            fi
        fi
    fi
}

# Function to start service
start_service() {
    print_message "\n启动服务..." "$BLUE"

    systemctl start "$SERVICE_NAME.service"

    # Wait for service to start
    sleep 2

    if systemctl is-active --quiet "$SERVICE_NAME.service"; then
        print_message "服务已成功启动！" "$GREEN"
    else
        print_message "服务启动失败，请检查日志" "$RED"
        print_message "使用命令查看日志: journalctl -u $SERVICE_NAME -n 50" "$YELLOW"
        exit 1
    fi
}

# Function to display post-installation info
display_info() {
    print_message "\n=== 安装完成 ===" "$GREEN"
    print_message "\n访问地址:" "$BLUE"

    if [ "$HOST" = "0.0.0.0" ]; then
        # Get local IP addresses
        LOCAL_IPS=$(hostname -I | tr ' ' '\n' | grep -v '^$')
        for IP in $LOCAL_IPS; do
            print_message "  http://$IP:$PORT" "$NC"
        done
    else
        print_message "  http://localhost:$PORT" "$NC"
    fi

    print_message "\n服务管理命令:" "$BLUE"
    print_message "  启动服务: sudo systemctl start $SERVICE_NAME" "$NC"
    print_message "  停止服务: sudo systemctl stop $SERVICE_NAME" "$NC"
    print_message "  重启服务: sudo systemctl restart $SERVICE_NAME" "$NC"
    print_message "  查看状态: sudo systemctl status $SERVICE_NAME" "$NC"
    print_message "  查看日志: sudo journalctl -u $SERVICE_NAME -f" "$NC"

    print_message "\n配置文件位置: $INSTALL_DIR/config.json" "$BLUE"
    print_message "数据库位置: $INSTALL_DIR/students.db" "$BLUE"
    print_message "上传文件位置: $INSTALL_DIR/uploads/" "$BLUE"

    print_message "\n默认管理员账号: admin" "$YELLOW"
    print_message "首次访问 /admin/login 设置管理员密码" "$YELLOW"
}

# Function to uninstall
uninstall() {
    print_message "\n=== 卸载学信网档案管理系统 ===" "$RED"

    read -p "确认要卸载吗？所有数据将被删除！(yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        print_message "卸载已取消" "$YELLOW"
        exit 0
    fi

    # Stop and disable service
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
    fi
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        systemctl disable "$SERVICE_NAME"
    fi

    # Remove service file
    rm -f "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload

    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
    fi

    # Remove user
    if id "$SERVICE_USER" &>/dev/null; then
        userdel "$SERVICE_USER"
    fi

    print_message "卸载完成" "$GREEN"
}

# Main installation flow
main() {
    print_message "=== 学信网档案管理系统安装程序 ===" "$BLUE"

    # Check if uninstall flag is passed
    if [ "$1" = "--uninstall" ]; then
        check_root
        uninstall
        exit 0
    fi

    # Pre-installation checks
    check_root
    detect_os
    check_dependencies

    # Interactive configuration
    configure_installation

    # Installation
    get_latest_release
    download_and_extract
    create_system_user
    create_config
    create_wrapper_script
    create_systemd_service
    configure_firewall

    # Start service
    if [[ "$AUTO_START" =~ ^[Yy]$ ]]; then
        start_service
    fi

    # Display post-installation information
    display_info
}

# Run main function
main "$@"