"""
配置管理模块

基于 Pydantic Settings 从环境变量或 `.env` 文件加载配置。
"""
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingConfig(BaseModel):
    """日志配置子模型

    Attributes:
        level: 日志级别（DEBUG / INFO / WARNING / ERROR / CRITICAL）
        file_path: 日志文件路径
        rotation: 日志轮转周期（如 "1 hour"、"100 MB"）
        retention: 日志保留时间（如 "7 days"）
        format: 控制台输出格式（"json" 或 "console"）
    """

    level: str = Field(default="INFO", description="日志级别")
    file_path: str = Field(
        default="logs/x-websocket.log", description="日志文件路径"
    )
    rotation: str = Field(default="1 hour", description="日志轮转周期")
    retention: str = Field(default="7 days", description="日志保留时间")
    format: str = Field(
        default="console",
        description='控制台日志格式："json"（生产环境）或 "console"（开发环境）',
    )


class Settings(BaseSettings):
    """应用配置

    优先级：环境变量 > .env 文件 > 默认值
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8765, description="服务器监听端口")
    debug: bool = Field(default=True, description="调试模式")

    # 日志配置（扁平字段，兼容 .env 中的 LOG_LEVEL）
    log_level: str = Field(default="INFO", description="日志级别")

    # 结构化日志配置（嵌套子模型）
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @property
    def effective_log_level(self) -> str:
        """返回实际生效的日志级别。

        优先使用扁平的 ``log_level`` 字段（向后兼容），若未显式设置则
        取 ``logging.level``。
        """
        return self.log_level or self.logging.level


# 全局配置实例
settings = Settings()