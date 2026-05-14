# syntax=docker/dockerfile:1.6
#
# 第二课堂活动通知系统 · 后端
# Python 3.12 + FastAPI + Selenium(Chromium 用于第二课堂网站爬取)
#

FROM python:3.12-slim-bookworm

# ---------- 1. 系统层依赖 ----------
# - chromium / chromium-driver:Selenium 爬虫使用
# - fonts-noto-cjk:渲染中文页面
# - tzdata:容器内使用本地时区
# - curl / ca-certificates:健康检查 + HTTPS 调用
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        fonts-noto-cjk \
        tzdata \
        curl \
        ca-certificates \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

# Selenium 4.x 需要知道 chromedriver 位置
ENV PATH="/usr/lib/chromium:${PATH}" \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---------- 2. Python 依赖(单独一层,改代码不会重装) ----------
COPY requirements.txt .
RUN pip install -r requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple

# ---------- 3. 项目代码 ----------
COPY . .

# 默认监听 8000,docker-compose 用非标准端口对外映射
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fs http://127.0.0.1:8000/health || exit 1

# 启动前先建表 + 写入默认 admin 账号,再起 uvicorn
CMD ["sh", "-c", "python init_db.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
