# ============================================================
# 阶段 1：构建前端（Node + pnpm）
# ============================================================
FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /build/frontend

# 先拷贝依赖文件 → 缓存 pnpm install 层
COPY frontend/package.json frontend/pnpm-lock.yaml* ./

RUN corepack enable && \
    pnpm install --frozen-lockfile --prod

# 再拷贝源码并构建
COPY frontend/ ./
RUN pnpm run build

# 只保留 dist 目录供下一阶段使用
# ============================================================
# 阶段 2：构建 Python 依赖（使用 uv）
# ============================================================
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS backend-deps

WORKDIR /build/backend

# 只拷贝锁文件和项目元数据 → 最大化缓存
COPY backend/pyproject.toml backend/uv.lock ./

# 只安装依赖（不安装项目本身、不装开发依赖）
# 使用 cache mount 加速下载
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --frozen --no-dev --no-install-project

# ============================================================
# 阶段 3：最终运行时镜像（最小化）
# ============================================================
FROM python:3.11-slim-bookworm AS runtime

# 安装运行时需要的系统包（nginx + 运行时库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    libmagic1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 从前端构建阶段拷贝静态文件
COPY --from=frontend-builder /build/frontend/dist /usr/share/nginx/html

# 从依赖阶段拷贝已安装的 .venv
COPY --from=backend-deps /build/backend/.venv /app/.venv

WORKDIR /app

# 拷贝应用代码（最后拷贝 → 改动最频繁，缓存失效最晚）
COPY backend/ ./

# 确保 PATH 包含虚拟环境
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Nginx 配置
COPY frontend/nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default && \
    nginx -t

# 启动脚本（前后端一起启动）
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 暴露端口
EXPOSE 80

# 推荐使用非 root 用户（可选，生产更安全）
# RUN useradd -m appuser
# USER appuser

CMD ["/start.sh"]