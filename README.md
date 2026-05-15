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

## 公网访问架构（frp 反向隧道）

小程序运行在公网，但 backend 部署在校园内网（10.5.80.8）。
通过 frp 反向隧道，让内网 backend 通过云端公网 IP 对外可访问：

```
小程序 / 公网客户端
   │ HTTP
   ▼
47.108.86.137 (阿里云, 域名 www.shuzhiweixin.top 备案中)
   ├─ :8000  → 云端 wechat 代理 (systemd 服务: 2ketang-wechat)
   ├─ :7443  → frps 控制面
   └─ :18000 → frps 反代，经隧道转发到 10.5.80.8:18000
                   │
                   ▼ (内网主动 dial out)
10.5.80.8 (校园内网, docker-compose)
   ├─ :18000 → backend (FastAPI)
   ├─ :18080 → frontend (nginx + Vue SPA)
   └─ mysql  (容器内, 不对外)
```

**关键约束**：ICP 备案绑定 IP 47.108.86.137。域名 DNS 只能指向已备案 IP。
内网通过 frpc 主动连接出去，跟备案路径一致，合规。

### 涉及的 systemd 服务

| 主机 | 服务 | 配置文件 | 说明 |
|---|---|---|---|
| 47.108.86.137 | `2ketang-wechat` | (代码 /root/2ketang/) | 微信通知代理 |
| 47.108.86.137 | `frps` | `/etc/frp/frps.toml` | frp 服务端 |
| 10.5.80.8 | `frpc` | `/etc/frp/frpc.toml` | frp 客户端，dial 到云端 |

frp token 在两端 `frp*.toml` 中。换 token 时两边都要改 + `systemctl restart`。

### 备案完成后要做的

1. DNS：`www.shuzhiweixin.top` A 记录指 `47.108.86.137`
2. 云端装 nginx，按路径分流：`/api/wechat/* → :8000`，`/api/* → :18000`
3. Let's Encrypt 配 HTTPS（Certbot 或 acme.sh）
4. 小程序业务域名白名单加 `https://www.shuzhiweixin.top`

## 开发约定

见 [CLAUDE.md](./CLAUDE.md)。开发进度记录在 [开发进度.md](./开发进度.md)。
