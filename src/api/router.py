"""API 路由聚合器。"""
from fastapi import APIRouter

from src.constants.constants import API_PREFIX
from .v1.health import router as health_router
from .v1.websocket import router as websocket_router
from .v1.ws_manage import router as ws_manage_router

router = APIRouter(prefix=API_PREFIX)

# 注册健康检查路由
router.include_router(health_router)

# 注册 WebSocket 端点（不出现在 Swagger 文档中）
router.include_router(websocket_router)

# 注册 WebSocket 管理路由（HTTP REST，出现在 Swagger 文档中）
router.include_router(ws_manage_router)

__all__ = ["router"]
