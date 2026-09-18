"""
FastAPI WebSocket 服务器主模块

提供 WebSocket 端点和消息路由，演示以下 WebSocket 核心机制：
- 回显（Echo）：服务器原样返回客户端消息
- 广播（Broadcast）：消息转发给所有已连接客户端
- 房间聊天（Room Chat）：消息仅转发给同一房间内的其他成员
- 心跳（Ping/Pong）：连接保活检测
"""
import asyncio
import json
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.logger import logger, setup_logging
from .connection.manager import ConnectionManager
from .models.message import MessageType

app = FastAPI(
    title="x-websocket",
    description="基于 WebSocket 协议的实时通信演示应用",
    version="0.1.0",
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
    logger.info(f"x-websocket 服务器启动，监听 {settings.host}:{settings.port}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """应用关闭"""
    logger.info("x-websocket 服务器关闭")


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
    await websocket.send_json({
        "type": MessageType.CONNECTED,
        "message": "连接已建立",
        "client_id": client_id,
        "timestamp": asyncio.get_running_loop().time(),
    })

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
    """解析消息并根据 type 字段路由到对应处理函数"""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        await _send_error(ws, "无效的 JSON 格式")
        return

    msg_type = data.get("type")

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
    content = data.get("content", "")
    logger.debug(f"[Echo] 客户端 {client_id}: {content}")
    await ws.send_json({
        "type": MessageType.ECHO,
        "content": content,
        "timestamp": asyncio.get_running_loop().time(),
    })


async def _handle_broadcast(ws: WebSocket, client_id: str, data: dict) -> None:
    """广播：将消息转发给所有已连接客户端（含发送者）"""
    content = data.get("content", "")
    logger.info(f"[Broadcast] 客户端 {client_id}: {content}")
    message = json.dumps({
        "type": MessageType.BROADCAST,
        "content": content,
        "sender": client_id,
        "timestamp": asyncio.get_running_loop().time(),
    })
    await manager.broadcast(message)


async def _handle_chat(ws: WebSocket, client_id: str, data: dict) -> None:
    """房间聊天：客户端自动加入房间，消息转发给同房间其他成员"""
    content = data.get("content", "")
    room_id = data.get("room_id", "default")

    # 自动加入房间
    await manager.join_room(room_id, client_id)

    logger.info(f"[Chat] 客户端 {client_id} → 房间 {room_id}: {content}")
    message = json.dumps({
        "type": MessageType.CHAT,
        "content": content,
        "room_id": room_id,
        "sender": client_id,
        "timestamp": asyncio.get_running_loop().time(),
    })
    await manager.broadcast_to_room(room_id, message, exclude=client_id)


async def _handle_ping(ws: WebSocket) -> None:
    """心跳：返回 Pong 响应"""
    await ws.send_json({
        "type": MessageType.PONG,
        "timestamp": asyncio.get_running_loop().time(),
    })


async def _send_error(ws: WebSocket, message: str) -> None:
    """发送错误消息"""
    await ws.send_json({
        "type": MessageType.ERROR,
        "message": message,
        "timestamp": asyncio.get_running_loop().time(),
    })


# ---------------------------------------------------------------------------
# HTTP 端点
# ---------------------------------------------------------------------------

@app.get("/")
async def root() -> dict:
    """根端点 — 返回服务基本信息"""
    return {
        "name": "x-websocket",
        "version": "0.1.0",
        "description": "基于 WebSocket 协议的实时通信演示应用",
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