"""
FastAPI 应用入口

创建应用实例、配置中间件，并注册 API 路由。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .constants.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION
from .core.config import settings
from .core.logger import logger, setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。

    在应用启动时初始化日志和核心组件，在应用关闭时执行清理操作。
    """
    setup_logging()

    logger.info(f"{APP_NAME} v{APP_VERSION} starting up...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.server.debug}")
    logger.info(f"Listening on: {settings.server.host}:{settings.server.port}")

    yield

    logger.info(f"{APP_NAME} shutting down...")


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
