from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.config import get_settings
from api.routes import chat, knowledge, model, tools

settings = get_settings()

TEST_MODE = os.environ.get("AICHAT_TEST_MODE", "0") == "1"

if TEST_MODE:
    print("\n" + "=" * 50)
    print("🔧 测试模式已启用 - 将返回模拟数据")
    print("=" * 50 + "\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("./vector_store", exist_ok=True)
    
    from services.llm import _warmup_all_models#预热模型
    asyncio.create_task(_warmup_all_models())
    
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="JeikChat智能客服系统API",
    lifespan=lifespan,
)

app.state.TEST_MODE = TEST_MODE

if TEST_MODE:
    from api.routes import mock as test_router
    app.include_router(test_router.router, prefix="/api", tags=["测试模式"])
    print("📦 测试路由已注册")


origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not TEST_MODE:
    app.include_router(chat.router, prefix="/api", tags=["聊天"])
    app.include_router(knowledge.router, prefix="/api", tags=["知识库"])
    app.include_router(model.router, prefix="/api", tags=["模型配置"])
    app.include_router(tools.router, prefix="/api", tags=["工具"])


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "test_mode": TEST_MODE
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "test_mode": TEST_MODE}
