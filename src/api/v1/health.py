"""
健康检查接口

本模块提供应用健康检查和版本信息查询接口，
用于服务监控、负载均衡健康探测和部署验证。

Endpoints:
    GET /health: 健康检查（返回数据库、缓存连通状态）
    GET /version: 版本信息
"""
from fastapi import APIRouter

from src.constants.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION
from src.services import message_service

router = APIRouter(tags=["健康检查"])



@router.get("/health")
async def health_check() -> dict[str, int | str]:
    """返回服务健康状态。"""
    return message_service.health()
