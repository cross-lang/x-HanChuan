#!/usr/bin/env python3
"""
通用数据模型

本模块定义了项目中所有请求/响应模型的公共基类和通用数据结构，
提供通用字段和校验规则。

基类列表：
    - ApiResponse: 标准 API 响应模型
    - PaginatedRequest: 分页请求模型
    - PaginatedResponse: 分页响应模型
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """标准 API 响应模型。

    统一包装所有 HTTP 响应，字段含义：
        code: HTTP 业务状态码（与 status 一致；4xx/5xx/2xx 标识业务结果）
        message: 响应描述（成功 "success"，错误为错误简述）
        data: 业务数据（成功时为业务对象，错误时为 None）
        timestamp: 响应时间戳（UTC）
        request_id: 请求追踪 ID

    Type Parameters:
        T: 业务数据类型，默认为 Any
    """

    code: int = Field(description="状态码")
    message: str = Field(description="响应描述")
    data: T | None = Field(default=None, description="业务数据")
    timestamp: str = Field(description="响应时间戳")
    request_id: str | None = Field(default=None, description="请求追踪 ID")

    model_config = ConfigDict(from_attributes=True)


class PaginatedRequest(BaseModel):
    """分页请求模型。

    提供统一的分页参数，所有需要分页的接口应使用此类。

    Attributes:
        page: 页码（从 1 开始）
        page_size: 每页记录数
    """

    page: int = Field(default=1, ge=1, description="页码（从 1 开始）")
    page_size: int = Field(default=20, ge=1, le=100, description="每页记录数")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型。

    提供统一的分页元数据，与数据列表配合使用。

    Attributes:
        items: 当前页数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页记录数
        total_pages: 总页数
    """

    items: list[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, ge=0, description="总记录数")
    page: int = Field(default=1, ge=1, description="当前页码")
    page_size: int = Field(default=20, ge=1, description="每页记录数")
    total_pages: int = Field(default=0, ge=0, description="总页数")

    model_config = ConfigDict(from_attributes=True)
