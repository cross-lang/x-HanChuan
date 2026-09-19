"""
WebSocket 连接管理器

负责管理所有 WebSocket 连接的生命周期，提供以下核心能力：
- 连接注册与注销（O(1) 断连清理）
- 点对点消息发送
- 全局广播
- 房间（Room）管理与房间内广播
- 基于令牌桶的速率限制
- 消息大小校验
"""
import time
from typing import Dict, Set, Optional

from fastapi import WebSocket

from src.core.logger import logger

# ============================================================
# 默认配置
# ============================================================

DEFAULT_MAX_MESSAGE_BYTES: int = 64 * 1024   # 单条消息上限 64 KB
DEFAULT_RATE_LIMIT_RPS: float = 20.0         # 每客户端每秒最大请求数
DEFAULT_RATE_LIMIT_BURST: int = 40           # 令牌桶突发容量


class ConnectionManager:
    """WebSocket 连接管理器

    维护所有活跃连接、房间映射关系以及每客户端速率限制状态。
    是服务器消息分发的核心组件。

    Attributes:
        active_connections: 已连接的客户端映射（client_id → WebSocket）
        rooms: 房间映射（room_id → 客户端 ID 集合）
        client_rooms: 反向索引（client_id → 加入的房间 ID 集合）
        max_message_bytes: 单条消息最大字节数
        rate_limit_rps: 每客户端每秒允许的最大消息数
        rate_limit_burst: 令牌桶突发容量
    """

    def __init__(
        self,
        *,
        max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES,
        rate_limit_rps: float = DEFAULT_RATE_LIMIT_RPS,
        rate_limit_burst: int = DEFAULT_RATE_LIMIT_BURST,
    ) -> None:
        self.active_connections: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, Set[str]] = {}
        self.client_rooms: Dict[str, Set[str]] = {}
        self.max_message_bytes = max_message_bytes
        self.rate_limit_rps = rate_limit_rps
        self.rate_limit_burst = rate_limit_burst

        # 速率限制状态：每客户端 [上次刷新时间, 剩余令牌数]
        self._rate_state: Dict[str, list[float]] = {}

    # ------------------------------------------------------------------
    # 连接生命周期
    # ------------------------------------------------------------------

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """注册新连接

        Args:
            websocket: WebSocket 连接对象
            client_id: 客户端唯一标识
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self._rate_state[client_id] = [time.monotonic(), float(self.rate_limit_burst)]
        logger.info(f"客户端 {client_id} 已连接，当前在线: {self.get_active_count()}")

    async def disconnect(self, client_id: str) -> None:
        """注销连接并从所有房间移除（O(1) 复杂度）

        Args:
            client_id: 客户端唯一标识
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"客户端 {client_id} 已断开，当前在线: {self.get_active_count()}")

        # 清理速率限制状态
        self._rate_state.pop(client_id, None)

        # 通过反向索引 O(1) 定位该客户端所在的所有房间
        for room_id in self.client_rooms.pop(client_id, set()):
            members = self.rooms.get(room_id)
            if members is None:
                continue
            members.discard(client_id)
            if not members:
                del self.rooms[room_id]
                logger.debug(f"房间 {room_id} 已空，自动移除")

    # ------------------------------------------------------------------
    # 消息校验 & 速率限制
    # ------------------------------------------------------------------

    def check_message_size(self, raw: str) -> bool:
        """校验原始消息是否超过大小上限

        Args:
            raw: 原始文本消息

        Returns:
            True 表示合法，False 表示超限
        """
        return len(raw.encode("utf-8")) <= self.max_message_bytes

    def check_rate_limit(self, client_id: str) -> bool:
        """令牌桶速率限制

        Args:
            client_id: 客户端 ID

        Returns:
            True 表示允许，False 表示需要限流
        """
        state = self._rate_state.get(client_id)
        if state is None:
            return True

        now = time.monotonic()
        elapsed = now - state[0]
        state[0] = now

        # 补充令牌
        state[1] = min(
            float(self.rate_limit_burst),
            state[1] + elapsed * self.rate_limit_rps,
        )

        if state[1] >= 1.0:
            state[1] -= 1.0
            return True
        return False

    # ------------------------------------------------------------------
    # 消息发送
    # ------------------------------------------------------------------

    async def send_personal(self, message: str, client_id: str) -> None:
        """向指定客户端发送消息

        Args:
            message: 消息内容（JSON 字符串）
            client_id: 目标客户端 ID
        """
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.error(f"发送消息给 {client_id} 失败: {e}")

    async def broadcast(
        self, message: str, exclude: Optional[str] = None
    ) -> None:
        """向所有已连接客户端广播消息

        Args:
            message: 消息内容（JSON 字符串）
            exclude: 排除的客户端 ID（通常排除发送者自身）
        """
        for cid, ws in self.active_connections.items():
            if cid == exclude:
                continue
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.error(f"广播消息给 {cid} 失败: {e}")

    # ------------------------------------------------------------------
    # 房间管理（双向索引维护）
    # ------------------------------------------------------------------

    async def join_room(self, room_id: str, client_id: str) -> None:
        """将客户端加入指定房间

        Args:
            room_id: 房间 ID
            client_id: 客户端 ID
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(client_id)

        if client_id not in self.client_rooms:
            self.client_rooms[client_id] = set()
        self.client_rooms[client_id].add(room_id)

        logger.info(
            f"客户端 {client_id} 加入房间 {room_id}，"
            f"房间人数: {len(self.rooms[room_id])}"
        )

    async def leave_room(self, room_id: str, client_id: str) -> None:
        """将客户端移出指定房间

        Args:
            room_id: 房间 ID
            client_id: 客户端 ID
        """
        if room_id in self.rooms and client_id in self.rooms[room_id]:
            self.rooms[room_id].discard(client_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
                logger.debug(f"房间 {room_id} 已空，自动移除")

        client_room_set = self.client_rooms.get(client_id)
        if client_room_set:
            client_room_set.discard(room_id)
            if not client_room_set:
                del self.client_rooms[client_id]

        logger.info(f"客户端 {client_id} 离开房间 {room_id}")

    async def broadcast_to_room(
        self, room_id: str, message: str, exclude: Optional[str] = None
    ) -> None:
        """向房间内所有成员广播消息

        Args:
            room_id: 房间 ID
            message: 消息内容（JSON 字符串）
            exclude: 排除的客户端 ID（通常排除发送者自身）
        """
        members = self.rooms.get(room_id, set())
        for cid in members:
            if cid == exclude:
                continue
            await self.send_personal(message, cid)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def get_active_count(self) -> int:
        """获取当前在线客户端数量"""
        return len(self.active_connections)

    def get_room_count(self, room_id: str) -> int:
        """获取指定房间的成员数量"""
        return len(self.rooms.get(room_id, set()))