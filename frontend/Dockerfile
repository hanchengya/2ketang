# syntax=docker/dockerfile:1.6
#
# 第二课堂活动通知系统 · 前端
# 多阶段构建:Node 构建 → nginx 静态托管
#

# ---------- Stage 1: build ----------
FROM node:20-alpine AS builder

WORKDIR /app

# 国内镜像加速
RUN npm config set registry https://registry.npmmirror.com

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build


# ---------- Stage 2: nginx 托管 + /api 反代 ----------
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
