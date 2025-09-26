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
DEFAULT_HOST="0.0.0.0"  # 默认允许公网访问
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
    print_message "  2) 允许公网访问 (0.0.0.0)" "$NC"
    read -p "请选择 (1-2, 默认: 2): " ACCESS_CHOICE

    case $ACCESS_CHOICE in
        1)
            HOST="127.0.0.1"
            print_message "已设置为仅本机访问" "$GREEN"
            ;;
        *)
            HOST="0.0.0.0"
            print_message "已设置为允许公网访问" "$GREEN"
            print_message "提示: 请确保防火墙已开放端口 $PORT" "$YELLOW"
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

    # Download release with better progress display
    print_message "下载地址: $DOWNLOAD_URL" "$YELLOW"

    # Check if curl is available (better progress display than wget)
    if command -v curl &> /dev/null; then
        print_message "使用 curl 下载（显示进度）..." "$BLUE"
        if ! curl -L --progress-bar --connect-timeout 30 --retry 3 --retry-delay 5 \
                  -o xuexinwang.tar.gz "$DOWNLOAD_URL"; then
            print_message "下载失败，尝试使用备用方法..." "$YELLOW"
            # Fallback to wget
            if ! wget --progress=bar:force --timeout=30 --tries=3 \
                     "$DOWNLOAD_URL" -O xuexinwang.tar.gz; then
                print_message "下载失败，请检查网络连接" "$RED"
                print_message "如果持续失败，您可以手动下载: $DOWNLOAD_URL" "$YELLOW"
                rm -rf $TEMP_DIR
                exit 1
            fi
        fi
    else
        print_message "使用 wget 下载（显示进度）..." "$BLUE"
        if ! wget --progress=bar:force --timeout=30 --tries=3 \
                 "$DOWNLOAD_URL" -O xuexinwang.tar.gz; then
            print_message "下载失败，请检查网络连接" "$RED"
            print_message "如果持续失败，您可以手动下载: $DOWNLOAD_URL" "$YELLOW"
            rm -rf $TEMP_DIR
            exit 1
        fi
    fi

    # Verify download
    if [ ! -f xuexinwang.tar.gz ]; then
        print_message "下载文件不存在，下载失败" "$RED"
        rm -rf $TEMP_DIR
        exit 1
    fi

    # Check file size (should be at least 1MB)
    FILE_SIZE=$(stat -c%s xuexinwang.tar.gz 2>/dev/null || stat -f%z xuexinwang.tar.gz 2>/dev/null)
    if [ "$FILE_SIZE" -lt 1048576 ]; then
        print_message "下载的文件过小，可能下载不完整" "$RED"
        rm -rf $TEMP_DIR
        exit 1
    fi

    print_message "下载完成，文件大小: $(($FILE_SIZE / 1048576)) MB" "$GREEN"

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

# Change to application directory
cd "$(dirname "$0")"

# Check if running from source or compiled
if [ -f "app.py" ]; then
    # Running from source - use Gunicorn
    echo "Starting with Gunicorn (production server)..."

    # Check if gunicorn is installed
    if ! command -v gunicorn &> /dev/null; then
        echo "Installing Gunicorn..."
        pip install gunicorn
    fi

    # Start with Gunicorn
    exec gunicorn -c gunicorn_config.py app:app
else
    # Running compiled version
    echo "Starting compiled version..."

    # Load configuration
    CONFIG_FILE="$(dirname "$0")/config.json"

    if [ -f "$CONFIG_FILE" ]; then
        # Use Python to parse JSON properly
        if command -v python3 &> /dev/null; then
            PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('port', 5000))")
            HOST=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('host', '0.0.0.0'))")
        else
            # Fallback to improved grep parsing
            PORT=$(grep -o '"port":[^,}]*' "$CONFIG_FILE" | sed 's/"port"://g' | tr -d '," ')
            HOST=$(grep -o '"host":"[^"]*' "$CONFIG_FILE" | sed 's/"host":"//g' | tr -d '"')
        fi

        # Validate values
        if [ -z "$PORT" ]; then
            PORT=5000
        fi
        if [ -z "$HOST" ]; then
            HOST="0.0.0.0"
        fi
    else
        PORT=5000
        HOST="0.0.0.0"
    fi

    # Start the application
    exec ./xuexinwang --host "$HOST" --port "$PORT"
fi
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

        # Check for iptables
        if command -v iptables &> /dev/null; then
            if ! iptables -L INPUT -n | grep -q "dpt:$PORT"; then
                read -p "是否添加iptables规则允许端口 $PORT？(y/n): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    iptables -I INPUT -p tcp --dport $PORT -j ACCEPT
                    # Try to save iptables rules
                    if command -v netfilter-persistent &> /dev/null; then
                        netfilter-persistent save
                    elif command -v iptables-save &> /dev/null; then
                        iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
                    fi
                    print_message "已添加iptables规则" "$GREEN"
                fi
            fi
        fi

        # Cloud provider security group reminder
        print_message "\n重要提示：" "$YELLOW"
        print_message "如果您使用的是云服务器（阿里云、腾讯云、AWS等），" "$YELLOW"
        print_message "请确保在云控制台的安全组/防火墙规则中开放端口 $PORT" "$YELLOW"
        print_message "这是最常见的无法访问原因！" "$RED"
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

# Function to update system
update_system() {
    print_message "\n=== 更新学信网档案管理系统 ===" "$BLUE"

    # Check if system is installed
    if [ ! -d "$INSTALL_DIR" ]; then
        print_message "系统未安装在 $INSTALL_DIR" "$RED"
        print_message "请先运行安装脚本" "$YELLOW"
        exit 1
    fi

    # Stop service
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_message "停止服务..." "$BLUE"
        systemctl stop "$SERVICE_NAME"
    fi

    # Backup current data
    print_message "备份当前数据..." "$BLUE"
    BACKUP_DIR="$INSTALL_DIR/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Backup database
    if [ -f "$INSTALL_DIR/students.db" ]; then
        cp "$INSTALL_DIR/students.db" "$BACKUP_DIR/"
        print_message "数据库已备份" "$GREEN"
    fi

    # Backup uploads
    if [ -d "$INSTALL_DIR/uploads" ]; then
        cp -r "$INSTALL_DIR/uploads" "$BACKUP_DIR/"
        print_message "上传文件已备份" "$GREEN"
    fi

    # Backup config
    if [ -f "$INSTALL_DIR/config.json" ]; then
        cp "$INSTALL_DIR/config.json" "$BACKUP_DIR/"
        print_message "配置文件已备份" "$GREEN"
    fi

    # Download latest version
    print_message "\n正在获取最新版本..." "$BLUE"
    get_latest_release

    # Download and extract new version
    TEMP_DIR=$(mktemp -d)
    cd $TEMP_DIR

    print_message "下载最新版本..." "$BLUE"
    if command -v curl &> /dev/null; then
        curl -L --progress-bar --connect-timeout 30 --retry 3 \
             -o xuexinwang.tar.gz "$DOWNLOAD_URL"
    else
        wget --progress=bar:force --timeout=30 --tries=3 \
             "$DOWNLOAD_URL" -O xuexinwang.tar.gz
    fi

    # Extract
    print_message "解压文件..." "$BLUE"
    tar -xzf xuexinwang.tar.gz

    # Update files
    print_message "更新文件..." "$BLUE"
    # Keep user data, update program files
    if [ -d "xuexinwang" ]; then
        # Update executable
        if [ -f "xuexinwang/xuexinwang" ]; then
            cp "xuexinwang/xuexinwang" "$INSTALL_DIR/"
            chmod +x "$INSTALL_DIR/xuexinwang"
        fi

        # Update Python files if they exist
        for file in app.py app_wrapper.py gunicorn_config.py requirements.txt fix_images.py; do
            if [ -f "xuexinwang/$file" ]; then
                cp "xuexinwang/$file" "$INSTALL_DIR/"
            fi
        done

        # Update templates and static files
        if [ -d "xuexinwang/templates" ]; then
            cp -r "xuexinwang/templates" "$INSTALL_DIR/"
        fi
        if [ -d "xuexinwang/xxda" ]; then
            cp -r "xuexinwang/xxda" "$INSTALL_DIR/"
        fi

        # Update start script
        if [ -f "xuexinwang/start.sh" ]; then
            cp "xuexinwang/start.sh" "$INSTALL_DIR/"
            chmod +x "$INSTALL_DIR/start.sh"
        else
            create_wrapper_script
        fi
    fi

    # Restore user data (already in place, just verify)
    print_message "验证用户数据..." "$BLUE"
    if [ ! -f "$INSTALL_DIR/students.db" ] && [ -f "$BACKUP_DIR/students.db" ]; then
        cp "$BACKUP_DIR/students.db" "$INSTALL_DIR/"
    fi
    if [ ! -d "$INSTALL_DIR/uploads" ] && [ -d "$BACKUP_DIR/uploads" ]; then
        cp -r "$BACKUP_DIR/uploads" "$INSTALL_DIR/"
    fi

    # Clean up
    cd /
    rm -rf $TEMP_DIR

    # Fix permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

    # Restart service
    print_message "\n重启服务..." "$BLUE"
    systemctl daemon-reload
    systemctl start "$SERVICE_NAME"

    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_message "更新成功！" "$GREEN"
        print_message "当前版本: $LATEST_RELEASE" "$GREEN"
        print_message "备份位置: $BACKUP_DIR" "$YELLOW"
    else
        print_message "服务启动失败，请检查日志" "$RED"
        print_message "使用命令查看日志: journalctl -u $SERVICE_NAME -n 50" "$YELLOW"
        print_message "备份位置: $BACKUP_DIR" "$YELLOW"
        exit 1
    fi
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

    # Check if update flag is passed
    if [ "$1" = "--update" ]; then
        check_root
        update_system
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