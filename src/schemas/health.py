#!/usr/bin/env python3
"""
健康检查数据模型

本模块定义了健康检查接口的请求和响应数据模型。

Classes:
    HealthResponse: 健康检查响应模型
    VersionResponse: 版本信息响应模型
"""


from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康检查响应模型。

    Attributes:
        status: 服务状态（"ok" 表示正常，"error" 表示异常）
        version: 应用版本号
        app: 应用名称
        environment: 运行环境
        database: 数据库连接状态
        cache: 缓存连接状态
    """

    status: str = Field(default="ok", description="服务状态")
    version: str = Field(description="应用版本号")
    app: str = Field(description="应用名称")
    environment: str = Field(description="运行环境")
    database: str | None = Field(default=None, description="数据库连接状态")
    cache: str | None = Field(default=None, description="缓存连接状态")


class VersionResponse(BaseModel):
    """版本信息响应模型。

    Attributes:
        version: 应用版本号
        api_version: API 版本号（如 "v1"），与路由前缀一致
    """

    version: str = Field(description="应用版本号")
    api_version: str = Field(default="v1", description="API 版本号")

    @classmethod
    def current(cls) -> "VersionResponse":
        """构造当前版本响应，api_version 从常量 API_PREFIX 自动推导。

        Returns:
            VersionResponse: 含最新版本号的响应模型
        """
        from src.constants import API_PREFIX, APP_VERSION

        api_version = API_PREFIX.rstrip("/").rsplit("/", 1)[-1] or "v1"
        return cls(version=APP_VERSION, api_version=api_version)
