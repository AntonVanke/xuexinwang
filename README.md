# 学籍信息管理系统

一个基于 Flask 的学籍信息管理系统，提供优雅的界面和完整的信息录入、查询功能。

## 功能特点

- 📝 **完整的信息录入**：支持学生基本信息、院校信息、专业信息等全方位录入
- 🖼️ **照片上传**：支持照片上传和实时预览
- ✅ **表单验证**：客户端实时验证，确保数据准确性
- 🔗 **便捷分享**：自动生成唯一链接和二维码
- 📱 **响应式设计**：完美支持移动端和桌面端
- 🎨 **现代化界面**：采用渐变色和卡片式设计

## 项目结构

```
xuexinwang/
├── app.py                 # 主应用文件（新）
├── main.py               # 旧版主文件（兼容）
├── config.py             # 配置文件
├── requirements.txt      # 依赖包列表
├── models/              # 数据模型
│   └── student.py       # 学生信息模型
├── utils/               # 工具类
│   └── id_generator.py  # ID生成器
├── templates/           # 模板文件
│   ├── form.html       # 表单页面
│   ├── success.html    # 提交成功页面
│   ├── student_detail.html  # 学生详情页面（新）
│   ├── detail.html     # 旧版详情页面（兼容）
│   ├── 404.html        # 404错误页面
│   └── error.html      # 500错误页面
├── static/             # 静态资源（新）
│   ├── css/           # 样式文件
│   ├── js/            # JavaScript文件
│   └── images/        # 图片资源
├── data/               # 数据存储（新）
└── detail_files/       # 旧版数据存储（兼容）
```

## 安装部署

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/xuexinwang.git
cd xuexinwang
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行应用

```bash
# 使用新的应用文件
python app.py

# 或使用旧版（兼容模式）
python main.py
```

应用将在 `http://localhost:48088` 启动

## 配置说明

在 `config.py` 中可以修改以下配置：

- `HOST`: 服务器地址（默认: 0.0.0.0）
- `PORT`: 端口号（默认: 48088）
- `DEBUG`: 调试模式（生产环境请设为 False）
- `SECRET_KEY`: 密钥（生产环境请修改）
- `MAX_CONTENT_LENGTH`: 最大上传文件大小（默认: 16MB）

## 环境变量

可以通过环境变量覆盖默认配置：

```bash
export SECRET_KEY="your-secret-key"
export DEBUG=False
export PORT=8080
```

## API 路径

- `/` - 表单页面（GET）
- `/submit` - 提交表单（POST）
- `/student/<id>` - 查看学生详情（GET）
- `/d/<id>` - 旧版查看链接（兼容）

## 技术栈

- **后端**: Flask 2.3.3
- **前端**: HTML5 + CSS3 + JavaScript
- **数据存储**: JSON文件
- **部署**: Gunicorn（生产环境）

## 开发说明

### 添加新功能

1. 在 `models/` 中创建数据模型
2. 在 `utils/` 中添加工具类
3. 在 `templates/` 中创建页面模板
4. 在 `app.py` 中添加路由

### 代码规范

- 使用 PEP 8 代码风格
- 添加适当的注释和文档字符串
- 保持代码模块化和可维护性

## 生产部署

### 使用 Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 注意事项

- 生产环境请修改 `SECRET_KEY`
- 建议使用 HTTPS 协议
- 定期备份 `data/` 目录中的数据
- 考虑使用数据库替代 JSON 文件存储（大规模使用时）

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。