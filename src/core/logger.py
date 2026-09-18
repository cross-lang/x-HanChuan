#!/usr/bin/env python3
"""
统一日志管理模块

本模块提供全局唯一日志实例，基于 loguru 实现，支持：
    - **JSON 结构化日志**（默认）：扁平 JSON 格式，适合 Loki / ELK / Datadog 收集
    - **彩色控制台格式**（开发环境）：LOGGING_FORMAT=console 切换
    - **自动注入 request_id**：通过 middleware ``logger.contextualize()`` 实现，
      一条请求从头到尾所有日志都带同一个 ID
    - 日志分级：DEBUG / INFO / WARNING / ERROR / CRITICAL
    - 文件始终输出 JSON（便于后续分析），控制台按配置切换
    - 日志轮转和自动清理（按小时切割）

Usage:
    from src.core.logger import logger, setup_logging

    # 在应用启动时调用一次
    setup_logging()

    # 在任意模块中使用（request_id 由中间件自动注入，无需手动 bind）
    logger.info("Application started")

    # 手动绑定额外上下文（仍然有效）
    logger.bind(user_id="u123").info("User action")
"""

import json as _json
import os
import sys

from loguru import logger as _logger

from src.constants import APP_NAME

# 清除 loguru 默认 handler，由 setup_logging 统一管理
_logger.remove()

_configured: bool = False

# ============================================================
# 常量
# ============================================================

_DEFAULT_REQUEST_ID: str = "-"

# ============================================================
# 彩色控制台格式（开发环境人可读）
# ============================================================

_CONSOLE_FORMAT: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<yellow>{extra[request_id]}</yellow> | "
    "<level>{message}</level>"
)


# ============================================================
# JSON 序列化（生产环境结构化日志）
# ============================================================


def _json_serializer(record: dict) -> str:
    """将 loguru 日志记录序列化为扁平 JSON 字符串。

    输出格式示例::

        {
            "timestamp": "2026-09-14T10:30:00.123456+00:00",
            "level": "INFO",
            "logger": "src.main",
            "function": "create_app",
            "line": 42,
            "message": "Application started",
            "request_id": "550e8400-e29b-41d4-a716-446655440000"
        }

    当存在异常时额外附加 exception 字段::

        {
            ...
            "exception": {
                "type": "ValueError",
                "value": "invalid literal"
            }
        }

    Args:
        record: loguru 内部日志记录字典

    Returns:
        JSON 字符串（不含尾部换行）
    """
    log_entry: dict[str, object] = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
        "request_id": record["extra"].get("request_id", _DEFAULT_REQUEST_ID),
    }
    if record["exception"] is not None:
        log_entry["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
        }
    return _json.dumps(log_entry, ensure_ascii=False)


def _json_formatter(record: dict) -> str:
    """loguru format 回调：将日志记录格式化为 JSON 行。

    loguru 允许 format 参数为一个可调用对象，该对象接收 record 字典，
    返回一个 format 字符串。这里我们把 JSON 存入 extra，再通过
    ``{extra[json_output]}`` 引用。

    Args:
        record: loguru 内部日志记录字典

    Returns:
        loguru 格式字符串
    """
    record["extra"]["json_output"] = _json_serializer(record) + "\n"
    return "{extra[json_output]}"


# ============================================================
# 初始化
# ============================================================


def setup_logging(
    level: str | None = None,
    file_path: str | None = None,
    rotation: str | None = None,
    retention: str | None = None,
    log_format: str | None = None,
) -> None:
    """初始化日志配置，全局只能调用一次。

    控制台输出格式由 ``log_format`` 决定：
        - ``"json"``    → JSON 结构化（生产默认，适合 Loki / ELK）
        - ``"console"`` → 彩色人可读（开发环境）

    文件输出**始终**为 JSON 格式，便于日志采集和分析。

    参数为 None 时从 Settings 加载默认值。在应用 lifespan 中调用。

    Args:
        level: 日志级别，如 DEBUG、INFO、WARNING、ERROR、CRITICAL
        file_path: 日志文件路径
        rotation: 日志轮转周期，如 "1 hour"、"1 day"、"100 MB"
        retention: 日志保留时间，如 "7 days"、"30 days"
        log_format: 控制台日志格式，"json" 或 "console"
    """
    global _configured

    if _configured:
        return

    from src.core.config import settings

    log_level: str = level or settings.logging.level
    log_file_path: str = file_path or settings.logging.file_path
    log_rotation: str = rotation or settings.logging.rotation
    log_retention: str = retention or settings.logging.retention
    fmt: str = (log_format or settings.logging.format).lower()
    use_json_console: bool = fmt == "json"

    # 确保日志目录存在
    log_dir: str = os.path.dirname(log_file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    _logger.remove()

    # ----------------------------------------------------------
    # 控制台输出
    # ----------------------------------------------------------
    if use_json_console:
        # JSON 格式：适合容器环境，stdout 被 Loki / Fluentd 采集
        _logger.add(
            sink=sys.stderr,
            format=_json_formatter,
            level=log_level,
            enqueue=True,
        )
    else:
        # 彩色格式：适合本地开发，人可读
        _logger.add(
            sink=sys.stderr,
            format=_CONSOLE_FORMAT,
            level=log_level,
            colorize=True,
            enqueue=True,
        )

    # ----------------------------------------------------------
    # 文件输出（始终 JSON，便于后续分析）
    # ----------------------------------------------------------
    _logger.add(
        sink=log_file_path,
        format=_json_formatter,
        level=log_level,
        rotation=log_rotation,
        retention=log_retention,
        compression="zip",
        enqueue=True,
    )

    # ----------------------------------------------------------
    # 兜底：确保所有日志记录都有 request_id 字段
    # middleware 的 contextualize 会在请求作用域内注入真实 ID，
    # 非请求上下文的日志使用默认 "-"
    # ----------------------------------------------------------
    _logger.configure(
        patcher=lambda record: record["extra"].setdefault(
            "request_id", _DEFAULT_REQUEST_ID
        )
    )

    _configured = True


def get_logger() -> object:
    """获取全局日志实例。

    Returns:
        loguru.Logger: 全局日志实例
    """
    return _logger


def get_log_file_path() -> str:
    """获取日志文件路径，按小时切割时使用项目名称作为前缀。

    Returns:
        str: 日志文件路径
    """
    from src.core.config import settings

    base_path: str = settings.logging.file_path
    if base_path:
        dir_path: str = os.path.dirname(base_path)
        ext: str = os.path.splitext(base_path)[1] or ".log"
        return os.path.join(dir_path, f"{APP_NAME}-{{time:YYYYMMDDHH}}{ext}")
    return f"logs/{APP_NAME}-{{time:YYYYMMDDHH}}.log"


logger = _logger

__all__ = ["logger", "setup_logging", "get_logger", "get_log_file_path"]