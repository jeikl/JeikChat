FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# 保持与本地相同的目录结构
WORKDIR /backend

# 安装系统依赖和 Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    libmagic1 \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件（利用缓存层）
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen

# 复制项目文件（保持与本地相同的目录结构）
COPY cli.py ./
COPY app/ ./app/
COPY api/ ./api/
COPY schemas/ ./schemas/
COPY services/ ./services/
COPY config/ ./config/
COPY agent/ ./agent/
COPY fileUntils/ ./fileUntils/
COPY __init__.py ./

# 激活虚拟环境
ENV PATH="/backend/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
