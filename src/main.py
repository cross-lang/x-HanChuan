"""
FastAPI 应用入口

创建应用实例、配置中间件、注册 API 路由，并提供 CLI 启动命令。
直接运行 ``uv run x-HanChuan`` 即可启动服务。
"""
import argparse
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


def main() -> None:
    """CLI 入口（pyproject.toml 中的 entry point）。"""
    parser = argparse.ArgumentParser(
        prog="x-HanChuan",
        description="x-HanChuan（汉川） — 基于 WebSocket 协议的实时通信服务",
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"x-HanChuan {APP_VERSION}",
    )
    parser.add_argument("--host", default="0.0.0.0", help="服务器监听地址（默认 0.0.0.0）")
    parser.add_argument("--port", default=8000, type=int, help="服务器监听端口（默认 8000）")
    parser.add_argument("--reload", action="store_true", help="启用热重载（开发模式）")
    args = parser.parse_args()

    import uvicorn

    setup_logging()

    print(f"x-HanChuan 服务器启动中...")
    print(f"  地址:     ws://{args.host}:{args.port}/api/v1/channel")
    print(f"  热重载:   {'是' if args.reload else '否'}")
    print(f"  API 文档: http://{args.host}:{args.port}/docs")

    logger.info(f"服务器启动中：{args.host}:{args.port}")

    uvicorn.run(
        "src.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
