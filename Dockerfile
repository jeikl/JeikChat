# ============================================================
# 阶段 1：构建前端（Node + pnpm）
# ============================================================
FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /build/frontend

# 1. 先拷贝 package.json 和 pnpm-lock.yaml
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# 2. 安装 pnpm
RUN npm install -g pnpm@latest-10

# 3. 安装依赖
RUN pnpm install --frozen-lockfile

# 4. 拷贝剩余源码
COPY frontend/ ./

# 5. 执行构建
RUN pnpm run build

# ============================================================
# 阶段 2：构建 Python 依赖（使用 uv）
# ============================================================
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS backend-deps

WORKDIR /build/backend

# 拷贝依赖管理文件
COPY backend/pyproject.toml backend/uv.lock ./

# 安装依赖
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --frozen --no-dev

# ============================================================
# 阶段 3：最终运行时镜像（最小化）
# ============================================================
FROM python:3.11-slim-bookworm AS runtime

# 安装运行时需要的系统包
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    libmagic1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 从前端构建阶段拷贝静态文件
COPY --from=frontend-builder /build/frontend/dist /usr/share/nginx/html

WORKDIR /backend

# 显式复制后端代码文件和文件夹（按字母顺序）
COPY backend/__init__.py ./
COPY backend/cli.py ./
COPY backend/pyproject.toml ./
COPY backend/uv.lock ./

# 复制文件夹
COPY backend/agent/ ./agent/
COPY backend/api/ ./api/
COPY backend/app/ ./app/
COPY backend/config/ ./config/
COPY backend/fileUntils/ ./fileUntils/
COPY backend/schemas/ ./schemas/
COPY backend/services/ ./services/

# 从依赖阶段拷贝已安装的 .venv
COPY --from=backend-deps /build/backend/.venv /backend/.venv

# 设置环境变量
ENV PATH="/backend/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/backend

# Nginx 配置
COPY frontend/ngix.conf /etc/nginx/sites-available/default
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default && \
    nginx -t

# 启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80

CMD ["/start.sh"]
