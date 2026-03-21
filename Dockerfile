# ============================================================
# JeikChat 前后端合并镜像
# 包含：Python后端(FastAPI) + Node.js前端构建 + Nginx
# ============================================================

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# ============================================================
# 第一阶段：安装系统依赖
# ============================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    libmagic1 \
    nginx \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g pnpm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# 第二阶段：构建前端
# ============================================================
WORKDIR /frontend-build

# 复制前端依赖文件
COPY frontend/package.json ./

# 使用 pnpm 安装依赖（更快）
RUN pnpm install

# 复制前端源码
COPY frontend/ ./

# 构建前端
RUN pnpm run build

# 将构建产物复制到 Nginx 目录
RUN cp -r dist/* /usr/share/nginx/html/

# 清理前端构建目录
RUN rm -rf /frontend-build

# ============================================================
# 第三阶段：配置后端
# ============================================================
WORKDIR /backend

# 复制后端依赖文件
COPY backend/pyproject.toml backend/uv.lock ./

# 安装后端依赖
RUN uv sync --frozen

# 复制后端项目文件
COPY backend/cli.py ./
COPY backend/app/ ./app/
COPY backend/api/ ./api/
COPY backend/schemas/ ./schemas/
COPY backend/services/ ./services/
COPY backend/config/ ./config/
COPY backend/agent/ ./agent/
COPY backend/fileUntils/ ./fileUntils/
COPY backend/__init__.py ./

# 激活虚拟环境并设置 Python 路径
ENV PATH="/backend/.venv/bin:$PATH"
ENV PYTHONPATH=/backend

# ============================================================
# 第四阶段：配置 Nginx
# ============================================================

# 复制 Nginx 配置
COPY frontend/nginx.conf /etc/nginx/sites-available/default

# 启用配置
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# 测试 Nginx 配置
RUN nginx -t

# ============================================================
# 第五阶段：启动脚本
# ============================================================
COPY start.sh /start.sh
RUN chmod +x /start.sh

# ============================================================
# 暴露端口和启动
# ============================================================

# 只暴露 Nginx 端口（80），后端通过内部代理访问
EXPOSE 80

# 数据卷挂载点
VOLUME ["/backend/config", "/backend/agent/knowledges", "/backend/agent/mcp"]

# 启动命令
CMD ["/start.sh"]
