# 学信网档案管理系统

一个基于Flask的学生档案管理系统，提供学生信息录入、查询、管理等功能。

## 功能特性

- 📝 学生信息录入和管理
- 🔍 身份证号重复检测
- 📱 图像采集码生成（二维码）
- 👤 管理员后台
- 📊 数据导出（CSV格式）
- 🖼️ 学生照片上传（限制5MB）
- 🔐 安全的文件命名（query_id-随机8位16进制）

## 快速开始

### 方式一：使用安装脚本（Linux，推荐）

```bash
curl -sSL https://raw.githubusercontent.com/AntonVanke/xuexinwang/main/install.sh | bash
```

安装脚本提供交互式配置：
- 自定义端口号
- 选择访问权限（仅本机/允许外网）
- 开机自启动配置
- 自动创建systemd服务

### 方式二：手动安装

1. 下载最新版本：
```bash
wget https://github.com/AntonVanke/xuexinwang/releases/latest/download/xuexinwang-linux-amd64.tar.gz
tar -xzf xuexinwang-linux-amd64.tar.gz
cd xuexinwang
```

2. 运行程序：
```bash
./xuexinwang --host 0.0.0.0 --port 5000
```

### 方式三：从源码运行

1. 克隆仓库：
```bash
git clone https://github.com/AntonVanke/xuexinwang.git
cd xuexinwang
```

2. 安装依赖：
```bash
pip install flask werkzeug pillow qrcode[pil]
```

3. 运行应用：
```bash
python app.py
```

## 配置说明

### 配置文件 (config.json)

```json
{
    "port": 5000,
    "host": "127.0.0.1",
    "debug": false
}
```

- `port`: 服务端口号（默认5000）
- `host`: 监听地址
  - `127.0.0.1`: 仅本机访问
  - `0.0.0.0`: 允许外部访问
- `debug`: 调试模式（生产环境请设为false）

### 系统服务管理

安装脚本会自动创建systemd服务，可使用以下命令管理：

```bash
# 启动服务
sudo systemctl start xuexinwang

# 停止服务
sudo systemctl stop xuexinwang

# 重启服务
sudo systemctl restart xuexinwang

# 查看服务状态
sudo systemctl status xuexinwang

# 查看服务日志
sudo journalctl -u xuexinwang -f

# 设置开机自启
sudo systemctl enable xuexinwang

# 取消开机自启
sudo systemctl disable xuexinwang
```

## 目录结构

```
xuexinwang/
├── xuexinwang          # 可执行文件
├── config.json         # 配置文件
├── students.db         # SQLite数据库
├── templates/          # HTML模板
├── xxda/              # 静态资源
└── uploads/           # 上传的图片
```

## 管理员功能

首次访问 `/admin/login` 设置管理员密码（最少8位）。

管理员功能包括：
- 查看所有学生信息
- 编辑学生信息
- 删除学生记录
- 导出数据为CSV
- 查看统计信息

## 安全建议

1. **防火墙配置**：如果允许外部访问，请配置防火墙规则
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 5000/tcp

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

2. **反向代理**：生产环境建议使用Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **数据备份**：定期备份 `students.db` 和 `uploads/` 目录

## 卸载

使用安装脚本安装的系统可以执行：
```bash
sudo /opt/xuexinwang/install.sh --uninstall
```

或手动卸载：
```bash
sudo systemctl stop xuexinwang
sudo systemctl disable xuexinwang
sudo rm -rf /opt/xuexinwang
sudo rm /etc/systemd/system/xuexinwang.service
sudo systemctl daemon-reload
```

## 故障排除

### 端口被占用
```bash
# 查看端口占用
sudo lsof -i :5000

# 或更改配置文件中的端口号
```

### 服务无法启动
```bash
# 查看详细错误日志
sudo journalctl -u xuexinwang -n 100 --no-pager
```

### 权限问题
```bash
# 确保文件权限正确
sudo chown -R xuexinwang:xuexinwang /opt/xuexinwang
sudo chmod +x /opt/xuexinwang/xuexinwang
```

## 开发

### 构建可执行文件

项目使用GitHub Actions自动构建，在发布新版本时自动触发：

```bash
git tag v1.0.1
git push origin v1.0.1
```

也可以手动构建：
```bash
pip install pyinstaller
pyinstaller --onefile \
  --name xuexinwang \
  --add-data "templates:templates" \
  --add-data "xxda:xxda" \
  app_wrapper.py
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题请提交Issue：https://github.com/AntonVanke/xuexinwang/issues