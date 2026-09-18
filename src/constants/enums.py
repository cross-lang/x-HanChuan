#!/usr/bin/env python3
"""业务枚举定义。

集中定义项目通用枚举类型，供 schemas / services / repositories 复用。
枚举值对齐数据库列定义，避免业务代码中出现魔法字符串。
"""

from enum import Enum
from src.constants.base import BaseEnum

class CommonStatus(Enum):
    """通用启用/停用状态（对齐 roles、permissions 等表的 status 列）。"""

    ENABLED = "enabled"
    DISABLED = "disabled"

class MessageType(str, Enum):
    """消息类型枚举

    每种类型对应一种 WebSocket 通信场景：
    - ECHO: 回显消息（服务器原样返回）
    - BROADCAST: 广播消息（转发给所有已连接客户端）
    - CHAT: 房间聊天消息（转发给同一房间内的其他客户端）
    - PING / PONG: 心跳检测
    - ERROR: 错误消息
    - CONNECTED: 连接确认消息
    """
    ECHO = "echo"
    BROADCAST = "broadcast"
    CHAT = "chat"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    CONNECTED = "connected"