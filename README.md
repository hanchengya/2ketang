# 第二课堂活动通知系统

FastAPI + Vue 3 + MySQL + Selenium 爬虫，自动从第二课堂平台抓取活动/学生/签到数据，给学生发邮件 / 微信订阅消息提醒。

## 目录结构

```
admin/
├── backend/              FastAPI 后端 + Selenium 爬虫
├── frontend/             Vue 3 + Vite 管理端（nginx 托管）
├── mysql-init/           MySQL 容器首次启动执行的 SQL
├── auto_login_system/    （历史：早期独立的自动登录脚本）
├── scripts/              一次性测试 / 检查 / 修复脚本
│   └── archive/          归档：旧 HTML、爬取产物
├── docker-compose.yml    三服务编排（mysql + backend + frontend）
├── .env                  实际运行用的环境变量（不进 git）
├── .env.docker.example   环境变量模板
├── 开发进度.md           开发进度（唯一）
└── 新需求.md             需求列表
```

## 启动（Docker）

```bash
# 1. 准备环境变量
cp .env.docker.example .env
# 编辑 .env，填入数据库密码、邮箱授权码、微信 secret 等

# 2. 启动三服务
docker compose up -d --build

# 3. 访问
# 前端：http://<host>:18080
# 后端 API（可选，正常走前端代理）：http://<host>:18000
```

默认管理员：`admin` / `admin123`（首次启动 init_db.py 自动创建）。

## 启动（本地开发）

后端：

```bash
cd backend
pip install -r requirements.txt
python init_db.py        # 建表 + 建默认 admin
python run.py            # uvicorn 监听 8000
```

前端：

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev              # vite 监听 5173
```

## 关联系统

- **云端微信通知代理** `http://47.108.86.137:8000/api/wechat`：
  内网后端调它发订阅消息；小程序也直连它。代码见 `backend/app/api/wechat.py`，
  通过 `WECHAT_NOTIFY_PROXY_URL` 配置。

- **微信小程序源码**：在仓库根目录 `微信小程序/`（不在本目录下）。

## 开发约定

见 [CLAUDE.md](./CLAUDE.md)。开发进度记录在 [开发进度.md](./开发进度.md)。
