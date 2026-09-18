#!/usr/bin/env python
"""
Heartbeat 心跳检测客户端

Ping/Pong 心跳机制：
  客户端定期发送 Ping → 服务器回复 Pong
  用于检测连接存活、测量往返延迟。

用法：
  uv run python examples/04_heartbeat.py
"""
import asyncio
import json
import time
import websockets


async def send_pings(ws, interval: float = 2.0) -> None:
    """定时发送 Ping 并计算延迟"""
    seq = 0
    while True:
        await asyncio.sleep(interval)
        seq += 1
        send_time = time.monotonic()
        await ws.send(json.dumps({"type": "ping", "seq": seq}))
        print(f"[Ping #{seq}] 已发送")

        # 等待 Pong 响应
        raw = await ws.recv()
        recv_time = time.monotonic()
        data = json.loads(raw)

        if data.get("type") == "pong":
            latency_ms = (recv_time - send_time) * 1000
            print(f"[Pong #{seq}] 收到响应，延迟 {latency_ms:.1f} ms")


async def main() -> None:
    uri = "ws://localhost:8765/api/v1/ws"

    async with websockets.connect(uri) as ws:
        # 接收连接确认
        connected = json.loads(await ws.recv())
        print(f"[客户端] 已连接，client_id = {connected['client_id']}")
        print(f"[客户端] 每 2 秒发送一次心跳，按 Ctrl+C 停止\n")

        try:
            await send_pings(ws, interval=2.0)
        except KeyboardInterrupt:
            print("\n[心跳检测结束]")


if __name__ == "__main__":
    asyncio.run(main())
