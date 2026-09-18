"""API 路由聚合器。"""
from fastapi import APIRouter

from ..constants.constants import API_PREFIX
from .v1.system import router as system_router
from .v1.websocket import router as websocket_router

router = APIRouter(prefix=API_PREFIX)
router.include_router(system_router)
router.include_router(websocket_router)

__all__ = ["router"]
