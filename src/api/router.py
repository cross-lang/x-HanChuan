"""API 路由聚合器。"""
from fastapi import APIRouter

from src.constants.constants import API_PREFIX
from .v1.system import router as system_router
from .v1.websocket import router as websocket_router

router = APIRouter(prefix=API_PREFIX)

# 注册系统管理路由
router.include_router(system_router)

# 注册WebSocket管理路由
router.include_router(websocket_router)

__all__ = ["router"]
