# 第二课堂活动通知系统 - 后端

基于FastAPI的后端API服务

## 环境要求

- Python 3.9+
- MySQL 5.7+
- ChromeDriver（用于Selenium爬虫）

## 安装步骤

### 1. 激活Python环境

```bash
# Windows
D:\Software_environment\miniconda\_conda.exe activate 2ketang
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 4. 初始化数据库

```bash
mysql -h 10.5.80.8 -u root -p 2ketang < database_schema.sql
```

### 5. 启动服务

```bash
python run.py
```

服务将在 http://localhost:8000 启动

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
backend/
├── app/
│   ├── api/              # API路由
│   ├── crawlers/         # 爬虫模块
│   ├── models/           # 数据模型
│   ├── schemas/          # Pydantic模型
│   ├── services/         # 业务服务
│   ├── tasks/            # 定时任务
│   ├── utils/            # 工具函数
│   ├── config.py         # 配置文件
│   ├── database.py       # 数据库连接
│   └── main.py           # FastAPI应用
├── requirements.txt      # Python依赖
├── run.py               # 启动脚本
└── database_schema.sql  # 数据库初始化脚本
```

## 测试

### 测试爬虫模块

```bash
# 测试登录
python -m app.crawlers.login

# 测试活动爬虫
python -m app.crawlers.activity_crawler

# 测试详情爬虫
python -m app.crawlers.detail_crawler

# 测试参与者爬虫
python -m app.crawlers.participant_crawler
```

### 测试邮件服务

```bash
python -m app.services.email_service
```

## 注意事项

1. **测试模式**: 默认开启TEST_MODE，不会实际发送邮件
2. **数据库连接**: 确保数据库配置正确
3. **ChromeDriver**: 确保ChromeDriver版本与Chrome浏览器版本匹配
4. **邮箱授权码**: 使用QQ邮箱的授权码，不是登录密码
