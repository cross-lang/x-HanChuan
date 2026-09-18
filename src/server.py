"""
FastAPI WebSocket 服务器主模块

提供 WebSocket 端点和消息路由，支持以下通信模式：
- 回显（Echo）：服务器原样返回客户端消息
- 广播（Broadcast）：消息转发给所有已连接客户端
- 房间聊天（Room Chat）：消息仅转发给同一房间内的其他成员
- 心跳（Ping/Pong）：连接保活检测
"""
import json
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .constants.constants import APP_NAME, APP_VERSION
from .core.logger import logger, setup_logging
from .connection.manager import ConnectionManager
from .constants.enums import MessageType
from .models.message import (
    BaseMessage,
    BroadcastMessage,
    ChatMessage,
    ConnectedMessage,
    EchoMessage,
    ErrorMessage,
    PongMessage,
)

app = FastAPI(
    title=APP_NAME,
    description="基于 WebSocket 协议的实时通信服务",
    version=APP_VERSION,
)

# CORS 中间件（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局连接管理器
manager = ConnectionManager()


@app.on_event("startup")
async def startup_event() -> None:
    """应用启动"""
    setup_logging()
    logger.info(f"x-HanChuan 服务器启动，监听 {settings.host}:{settings.port}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """应用关闭"""
    logger.info("x-HanChuan 服务器关闭")


# ---------------------------------------------------------------------------
# WebSocket 端点
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 主端点

    连接建立后自动分配 client_id，随后进入消息循环，
    根据消息类型（type 字段）分发到对应的处理逻辑。
    """
    client_id = str(uuid.uuid4())[:8]
    await manager.connect(websocket, client_id)

    # 发送连接确认
    connected = ConnectedMessage(message="连接已建立", client_id=client_id)
    await websocket.send_json(connected.model_dump())

    try:
        while True:
            raw = await websocket.receive_text()
            await _dispatch(websocket, client_id, raw)
    except WebSocketDisconnect:
        logger.info(f"客户端 {client_id} 主动断开")
    except Exception as e:
        logger.error(f"客户端 {client_id} 异常: {e}")
    finally:
        await manager.disconnect(client_id)


# ---------------------------------------------------------------------------
# 消息分发
# ---------------------------------------------------------------------------

async def _dispatch(ws: WebSocket, client_id: str, raw: str) -> None:
    """解析消息并根据 type 字段路由到对应处理函数

    先用 BaseMessage 校验 JSON 格式与 type 字段，再分发到具体处理函数。
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        await _send_error(ws, "无效的 JSON 格式")
        return

    try:
        base = BaseMessage.model_validate(data)
    except Exception:
        await _send_error(ws, "消息格式校验失败")
        return

    msg_type = base.type

    if msg_type == MessageType.ECHO:
        await _handle_echo(ws, client_id, data)
    elif msg_type == MessageType.BROADCAST:
        await _handle_broadcast(ws, client_id, data)
    elif msg_type == MessageType.CHAT:
        await _handle_chat(ws, client_id, data)
    elif msg_type == MessageType.PING:
        await _handle_ping(ws)
    else:
        await _send_error(ws, f"未知的消息类型: {msg_type}")


# ---------------------------------------------------------------------------
# 各类型消息处理
# ---------------------------------------------------------------------------

async def _handle_echo(ws: WebSocket, client_id: str, data: dict) -> None:
    """回显：将消息原样返回给发送者"""
    try:
        msg = EchoMessage.model_validate(data)
    except Exception:
        await _send_error(ws, "Echo 消息格式错误")
        return
    logger.debug(f"[Echo] 客户端 {client_id}: {msg.content}")
    response = EchoMessage(content=msg.content)
    await ws.send_json(response.model_dump())


async def _handle_broadcast(ws: WebSocket, client_id: str, data: dict) -> None:
    """广播：将消息转发给所有已连接客户端（含发送者）"""
    try:
        msg = BroadcastMessage.model_validate(data)
    except Exception:
        await _send_error(ws, "Broadcast 消息格式错误")
        return
    logger.info(f"[Broadcast] 客户端 {client_id}: {msg.content}")
    response = BroadcastMessage(content=msg.content, sender=client_id)
    await manager.broadcast(response.model_dump_json())


async def _handle_chat(ws: WebSocket, client_id: str, data: dict) -> None:
    """房间聊天：客户端自动加入房间，消息转发给同房间其他成员"""
    try:
        msg = ChatMessage.model_validate(data)
    except Exception:
        await _send_error(ws, "Chat 消息格式错误")
        return

    # 自动加入房间
    await manager.join_room(msg.room_id, client_id)

    logger.info(f"[Chat] 客户端 {client_id} → 房间 {msg.room_id}: {msg.content}")
    response = ChatMessage(
        content=msg.content, room_id=msg.room_id, sender=client_id
    )
    await manager.broadcast_to_room(
        msg.room_id, response.model_dump_json(), exclude=client_id
    )


async def _handle_ping(ws: WebSocket) -> None:
    """心跳：返回 Pong 响应"""
    response = PongMessage()
    await ws.send_json(response.model_dump())


async def _send_error(ws: WebSocket, message: str) -> None:
    """发送错误消息"""
    response = ErrorMessage(message=message)
    await ws.send_json(response.model_dump())


# ---------------------------------------------------------------------------
# HTTP 端点
# ---------------------------------------------------------------------------

@app.get("/")
async def root() -> dict:
    """根端点 — 返回服务基本信息"""
    return {
        "name": "x-HanChuan",
        "version": "0.1.0",
        "description": "基于 WebSocket 协议的实时通信服务",
        "ws_endpoint": "/ws",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict:
    """健康检查端点"""
    return {
        "status": "healthy",
        "active_connections": manager.get_active_count(),
        "rooms": len(manager.rooms),
    }