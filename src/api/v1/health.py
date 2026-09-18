"""
健康检查接口

本模块提供应用健康检查和版本信息查询接口，

Endpoints:
    GET /health: 健康检查
    GET /version: 版本信息
"""
from fastapi import APIRouter

from src.constants.constants import APP_NAME, APP_VERSION
from src.core.config import settings
from src.schemas.health import HealthResponse, VersionResponse

router = APIRouter(tags=["api/v1/health"])


@router.get("/health", summary="健康检查")
async def health_check() -> HealthResponse:
    """健康检查。"""
    environment = "development" if settings.debug else "production"
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        app=APP_NAME,
        environment=environment,
    )


@router.get("/version", summary="版本信息")
async def version() -> VersionResponse:
    """版本信息。"""
    return VersionResponse.current()
