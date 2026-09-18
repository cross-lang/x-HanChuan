"""API 路由聚合器。"""
from fastapi import APIRouter

from src.constants.constants import API_PREFIX
from .v1.health import router as health_router
from .v1.message import router as message_router

router = APIRouter(prefix=API_PREFIX)

# 注册健康检查路由
router.include_router(health_router)

# 注册消息路由（WebSocket 通信端点 + 管理接口）
router.include_router(message_router)

__all__ = ["router"]
