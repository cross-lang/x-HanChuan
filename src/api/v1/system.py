"""系统 API 路由。"""
from fastapi import APIRouter

from ...constants.constants import APP_NAME, APP_VERSION
from ...services import message_service

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    """返回服务基本信息。"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": "基于 WebSocket 协议的实时通信服务",
        "ws_endpoint": "/api/v1/ws",
        "docs": "/docs",
    }


@router.get("/health")
async def health_check() -> dict[str, int | str]:
    """返回服务健康状态。"""
    return message_service.health()
