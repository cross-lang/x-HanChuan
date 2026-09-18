#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置管理

支持从环境变量和 YAML 配置文件读取配置，使用 dataclass 描述各配置段。
配置优先级：环境变量 > 环境特定配置(config.{env}.yaml) > 默认配置(config.yaml) > 代码默认值。

Usage:
    from src.core.config import settings
    port = settings.server.port
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import yaml

from src.constants import (
    DEFAULT_CONFIG_DIR,
    ENV_DEVELOPMENT,
    ENV_PRODUCTION,
    ENV_TESTING,
)


# ============================================================
# 辅助函数
# ============================================================


def _to_bool(value: str | None) -> bool:
    """将字符串转换为布尔值。"""
    return value.lower() == "true" if value else False


def _to_int(value: str | None, default: int = 0) -> int:
    """将字符串转换为整数。"""
    return int(value) if value else default


def _find_project_root() -> Path:
    """向上查找项目根目录（包含 pyproject.toml 的目录）。"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return current.parent.parent


# ============================================================
# Dataclass 配置段
# ============================================================


@dataclass
class ServerConfig:
    """服务器配置。"""

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True


@dataclass
class LoggingConfig:
    """日志配置。

    format:
        "json"    — 结构化 JSON 日志，适合 Loki / ELK 收集（生产默认）
        "console" — 彩色人可读格式，适合本地开发
    """

    level: str = "INFO"
    format: str = "console"
    file_path: str = "logs/x-HanChuan-{time:YYYYMMDDHH}.log"
    rotation: str = "1 hour"
    retention: str = "7 days"
    compression: str = "zip"
    console_output: bool = True


@dataclass
class CORSConfig:
    """跨域配置。"""

    enabled: bool = True
    origins: list[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: list[str] = field(default_factory=lambda: ["*"])
    allow_headers: list[str] = field(default_factory=lambda: ["*"])


# ============================================================
# 环境变量 → YAML 配置段 映射
# ============================================================

_ENV_SECTION_MAP: dict[str, tuple[str, list[str]]] = {
    "server": ("SERVER_", ["host", "port", "debug"]),
    "logging": (
        "LOGGING_",
        ["level", "format", "file_path", "rotation", "retention", "compression", "console_output"],
    ),
    "cors": (
        "CORS_",
        ["enabled", "origins", "allow_credentials", "allow_methods", "allow_headers"],
    ),
}


# ============================================================
# 核心配置类
# ============================================================


class Settings:
    """应用全局配置类。

    配置加载优先级（从高到低）：
        1. 环境变量
        2. 环境特定 YAML 配置（config.{env}.yaml）
        3. 默认 YAML 配置（config.yaml）
        4. 代码中的默认值

    Attributes:
        app_env: 当前运行环境
        server: 服务器配置
        logging: 日志配置
        cors: 跨域配置
    """

    def __init__(self) -> None:
        """初始化配置。"""
        self._config: dict[str, Any] = self._load_config()
        self._parse_config()

    # ----------------------------------------------------------
    # 配置加载
    # ----------------------------------------------------------

    def _load_config(self) -> dict[str, Any]:
        """加载配置，优先级：环境变量 > YAML 文件 > 默认值。"""
        config = self._get_default_config()
        self._load_from_yaml(config)
        self._load_from_env(config)
        return config

    def _get_default_config(self) -> dict[str, Any]:
        """返回所有配置段的代码默认值。"""
        return {
            "app_env": ENV_DEVELOPMENT,
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": True,
            },
            "logging": {
                "level": "INFO",
                "format": "console",
                "file_path": "logs/x-HanChuan-{time:YYYYMMDDHH}.log",
                "rotation": "1 hour",
                "retention": "7 days",
                "compression": "zip",
                "console_output": True,
            },
            "cors": {
                "enabled": True,
                "origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            },
        }

    def _merge_config(self, base: dict[str, Any], override: dict[str, Any]) -> None:
        """递归合并配置字典，override 中的值覆盖 base 中的同名键。"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _load_from_yaml(self, config: dict[str, Any]) -> None:
        """从 YAML 文件加载配置。

        先加载默认 config.yaml，再加载 config.{env}.yaml 进行深度覆盖。
        """
        project_root = _find_project_root()
        config_dir = project_root / DEFAULT_CONFIG_DIR

        # 先加载项目根目录的 .env，使其中的 APP_ENV 可用于选择环境配置。
        env_dot_file = project_root / ".env"
        if env_dot_file.exists():
            try:
                from dotenv import load_dotenv

                load_dotenv(env_dot_file, override=False)
            except Exception as e:
                print(f"Warning: Cannot load .env file {env_dot_file}: {e}")

        # 1. 加载默认配置
        default_file = config_dir / "config.yaml"
        if default_file.exists():
            try:
                with open(default_file, encoding="utf-8") as f:
                    default_cfg = yaml.safe_load(f) or {}
                if isinstance(default_cfg, dict):
                    self._merge_config(config, default_cfg)
            except Exception as e:
                print(f"Warning: Cannot load config file {default_file}: {e}")

        # 2. 加载环境特定配置（覆盖默认配置）
        app_env = os.environ.get("APP_ENV", config.get("app_env", ENV_DEVELOPMENT))
        env_file = config_dir / f"config.{app_env}.yaml"
        if env_file.exists():
            try:
                with open(env_file, encoding="utf-8") as f:
                    env_cfg = yaml.safe_load(f) or {}
                if isinstance(env_cfg, dict):
                    self._merge_config(config, env_cfg)
            except Exception as e:
                print(f"Warning: Cannot load config file {env_file}: {e}")

    def _load_from_env(self, config: dict[str, Any]) -> None:
        """从环境变量加载配置，覆盖 YAML 和默认值。

        映射规则：
            APP_ENV       → app_env
            SERVER_HOST   → server.host
            … 以此类推
        """
        # 顶层 app_env
        if value := os.environ.get("APP_ENV"):
            config["app_env"] = value

        # 各配置段
        for section_name, (prefix, keys) in _ENV_SECTION_MAP.items():
            if section_name not in config:
                continue
            section = config[section_name]
            for key in keys:
                env_key = f"{prefix}{key.upper()}"
                value = os.environ.get(env_key)
                if value is None:
                    continue
                # 根据默认值类型进行转换
                default_val = section.get(key)
                if isinstance(default_val, bool):
                    section[key] = _to_bool(value)
                elif isinstance(default_val, int):
                    section[key] = _to_int(value)
                elif isinstance(default_val, list):
                    section[key] = [v.strip() for v in value.split(",")]
                else:
                    section[key] = value

    # ----------------------------------------------------------
    # 解析到 dataclass
    # ----------------------------------------------------------

    def _parse_config(self) -> None:
        """将原始配置字典解析为 dataclass 实例。"""
        self.app_env: str = self._config.get("app_env", ENV_DEVELOPMENT)

        self.server = ServerConfig(**self._config.get("server", {}))
        self.logging = LoggingConfig(**self._config.get("logging", {}))

        # CORS 配置（嵌套列表字段需要特殊处理）
        cors_raw = self._config.get("cors", {})
        self.cors = CORSConfig(
            enabled=cors_raw.get("enabled", True),
            origins=cors_raw.get("origins", ["*"]),
            allow_credentials=cors_raw.get("allow_credentials", True),
            allow_methods=cors_raw.get("allow_methods", ["*"]),
            allow_headers=cors_raw.get("allow_headers", ["*"]),
        )

    # ----------------------------------------------------------
    # 环境判断
    # ----------------------------------------------------------

    @property
    def is_development(self) -> bool:
        """是否为开发环境。"""
        return self.app_env == ENV_DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """是否为测试环境。"""
        return self.app_env == ENV_TESTING

    @property
    def is_production(self) -> bool:
        """是否为生产环境。"""
        return self.app_env == ENV_PRODUCTION

    # ----------------------------------------------------------
    # 配置校验
    # ----------------------------------------------------------

    def validate(self) -> None:
        """验证配置合法性，配置错误直接阻断程序启动。

        生产环境额外校验：
            - 调试模式必须关闭
            - CORS origins 不能为 '*'

        Raises:
            ValueError: 配置不合法时抛出
        """
        if self.is_production:
            if self.server.debug:
                raise ValueError("DEBUG mode must be disabled in production")

            if "*" in self.cors.origins:
                raise ValueError(
                    "CORS origins 在生产环境禁止配置为 '*'，请指定可信来源列表"
                )

    # ----------------------------------------------------------
    # 热重载
    # ----------------------------------------------------------

    def reload(self) -> None:
        """重新加载全部配置（YAML + 环境变量），并重新校验。"""
        self._config = self._load_config()
        self._parse_config()
        self.validate()


# ============================================================
# 全局单例
# ============================================================

settings: Final[Settings] = Settings()