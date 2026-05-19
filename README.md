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

## 公网访问架构（Caddy + frp 反向隧道）

域名 `www.shuzhiweixin.top` 已备案，挂在云端 47.108.86.137。
公网入口统一走 HTTPS，Caddy 自动签发 / 续签 Let's Encrypt 证书，按路径分流：

```
小程序 / 公网客户端
   │ HTTPS
   ▼
https://www.shuzhiweixin.top   (DNS → 47.108.86.137:443)
   │
   ▼  Caddy 反代 (路径优先级: /api/wechat/* > /api/*)
   ├─ /api/wechat/*  → 127.0.0.1:8000   (本机 systemd: 2ketang-wechat)
   └─ /api/*         → 127.0.0.1:18000  (frps 反代, 经隧道转到内网 backend)
                          │
                          ▼ (frpc 主动 dial out)
                       10.5.80.8 (校园内网)
                          ├─ :18000 → backend (FastAPI)
                          ├─ :18080 → frontend (nginx + Vue SPA)
                          └─ mysql  (容器内, 不对外)
```

ICP 备案绑定 47.108.86.137。域名 DNS 只能指向已备案 IP。
内网通过 frpc 主动连接出去,跟备案路径一致,合规。

### 涉及的 systemd 服务

| 主机 | 服务 | 配置文件 | 说明 |
|---|---|---|---|
| 47.108.86.137 | `caddy` | `/etc/caddy/Caddyfile` | 公网入口, HTTPS 终结, 路径分流 |
| 47.108.86.137 | `2ketang-wechat` | (代码 /root/2ketang/) | 微信通知代理 (Caddy 上游) |
| 47.108.86.137 | `frps` | `/etc/frp/frps.toml` | frp 服务端, 把内网 backend 反向暴露到本机 :18000 |
| 10.5.80.8 | `frpc` | `/etc/frp/frpc.toml` | frp 客户端, dial 到云端 :7443 |

### 阿里云轻量应用安全组规则

| 端口 | 用途 |
|---|---|
| 22 | SSH |
| 80, 443 | Caddy 入口 (HTTPS) |
| 8000 | 旧版微信代理直连入口 (向前兼容, 内网用) |
| 7443 | frps 控制面 (frpc 拨号) |
| 18000 | frps 反代业务面 (向前兼容, 也可移除让流量统一走 Caddy) |

### 小程序业务域名白名单

微信公众平台 → 开发管理 → 开发设置 → 服务器域名 →
request 合法域名加 `https://www.shuzhiweixin.top`。

## "报名活动" 跳学校平台 (个人主体硬限制 → 复制链接方案)

小程序主体是**个人开发者**, 微信硬性限制:

> 个人主体小程序自 2017 年起不允许使用 `<web-view>` 组件, 公众平台后台
> 不显示"业务域名"设置入口。

这是 WeChat 平台规则, 跟微信认证 / 小程序备案是否完成无关。**永久限制**。

### 当前方案: 复制链接 + 微信内粘贴打开

`pages/activity/detail` 点 "报名活动" → `wx.setClipboardData` 把
`https://www.shuzhiweixin.top/enroll/<act_id>` 复制到剪贴板 →
`wx.showModal` 提示用户在微信"文件传输助手"粘贴并点击 → 微信识别为可点击
链接 → 用内置浏览器打开 → 走 Caddy 302 跳到 `2ketang.svtcc.edu.cn` 报名页。

体验上学生多 1-2 步, 但功能 100% 可用, 学生平台的登录 cookie 会保留
(微信内置浏览器是有 cookie 持久化的)。

### 想要"无感跳转"必须升级主体

唯一办法: 让学校 (或学院) 作为主体重新注册一个小程序, 走"单位主体微信认证"
(300 元/年, 需要单位营业执照 / 组织机构代码)。然后:

1. 业务域名添加 `https://www.shuzhiweixin.top`, 下载 `MP_verify_xxx.txt`
2. 校验文件放到 Caddy 静态目录 `/var/www/wechat-verify/` (已存在)
3. 微信后台校验通过
4. 小程序 `pages/activity/detail/detail.js` 的 `openEnrollment` 换回:
   ```js
   wx.navigateTo({ url: '/pages/webview/webview?url=' + encodeURIComponent(url) })
   ```

代码层面 `pages/webview/*` 容器页和 Caddy `/enroll/{id}` 302 都保留着, 升级
主体后改一行就能切回。但不升级主体, 永远走"复制链接"方案。

## 开发约定

见 [CLAUDE.md](./CLAUDE.md)。开发进度记录在 [开发进度.md](./开发进度.md)。
