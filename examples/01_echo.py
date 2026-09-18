#!/usr/bin/env python
"""
Echo 回显客户端

基础 WebSocket 通信模式：
  客户端发送消息 → 服务器原样返回

用法：
  uv run python examples/01_echo.py
"""
import asyncio
import json
import websockets


async def main() -> None:
    uri = "ws://localhost:8000/api/v1/channel"

    async with websockets.connect(uri) as ws:
        # 接收连接确认消息
        connected = json.loads(await ws.recv())
        print(f"[客户端] 已连接，client_id = {connected['client_id']}")

        # 发送 Echo 消息
        messages = ["你好，WebSocket！", "这是第二条消息", "Echo 测试完毕"]
        for msg in messages:
            await ws.send(json.dumps({"type": "echo", "content": msg}))
            print(f"[客户端] 发送 → {msg}")

            # 接收服务器回显
            response = json.loads(await ws.recv())
            print(f"[客户端] 收到 ← {response['content']}")

        print("\n[Echo 完成]")


if __name__ == "__main__":
    asyncio.run(main())
