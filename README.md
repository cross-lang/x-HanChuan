# x-websocket

`x-websocket`是一个基于 WebSocket 协议的实时通信服务，采用 FastAPI 构建。

## 核心特征

- **Echo 回显** — 最基础的 WebSocket 通信：客户端发送，服务器原样返回
- **Broadcast 广播** — 一对多通信：消息转发给所有已连接客户端
- **Room Chat 房间聊天** — 房间机制：消息仅转发给同一房间内的其他成员
- **Heartbeat 心跳** — Ping/Pong 保活检测与延迟测量
- **CLI 工具** — 内置 `x-websocket` 命令行工具，一键启动服务器
- **配置驱动** — 基于 Pydantic Settings 的 `.env` 配置管理，类型安全，开箱即用

## 项目结构

```
x-websocket/
├── src/                        # 源码根目录
│   ├── __init__.py             # 包元数据与版本信息
│   ├── __main__.py             # CLI 入口（Click 命令组）
│   ├── server.py               # FastAPI 应用，WebSocket 端点与消息路由
│   ├── connection/             # 连接管理
│   │   ├── __init__.py
│   │   └── manager.py          # WebSocket 连接管理器（注册/注销/广播/房间）
│   ├── core/                   # 核心基础设施
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings 配置类
│   │   └── logger.py           # 日志配置
│   └── models/                 # 数据模型
│       ├── __init__.py
│       └── message.py          # Pydantic 消息模型
├── examples/                   # 示例代码（由浅入深）
│   ├── 01_echo.py              # Echo 回显示例
│   ├── 02_broadcast.py         # 广播示例
│   ├── 03_room_chat.py         # 房间聊天示例
│   └── 04_heartbeat.py         # 心跳检测示例
├── pyproject.toml              # 项目配置与依赖声明
├── uv.toml                     # uv 包管理器配置
├── Dockerfile                  # Docker 多阶段构建
├── docker-compose.yml          # Docker Compose 编排
├── config.yaml.example         # YAML 配置示例（参考）
├── .env.example                # 环境变量示例
├── LICENSE                     # MIT 许可证
└── README.md
```

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    客户端层 (Client)                  │
│         WebSocket Client / CLI / 浏览器               │
└──────────────────────┬──────────────────────────────┘
                       │ ws:// / wss://
                       ▼
┌─────────────────────────────────────────────────────┐
│                   接入层 (Gateway)                    │
│              FastAPI + WebSocket /ws 端点              │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
        ┌────────┐┌────────┐┌────────┐
        │  Echo  ││Broadcast││  Chat  │   消息处理
        │  回显   ││  广播   ││ 房间聊天 │
        └────────┘└────────┘└────────┘
                       │
              ┌────────┴────────┐
              │ ConnectionManager│               连接管理
              │  (连接/房间/广播)  │
              └────────┬────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│                  基础设施层 (Infra)                    │
│     Config (Pydantic Settings)  │  Logger  │  CLI    │
└─────────────────────────────────────────────────────┘
```

### 消息处理流程

```
客户端发送 JSON 消息
        │
        ▼
  ┌─────────────┐
  │  解析 JSON   │─── 无效 → 返回 ErrorMessage
  └──────┬──────┘
         │ type 字段
    ┌────┼────┬────────┐
    ▼    ▼    ▼        ▼
  echo  broadcast  chat   ping
    │    │         │       │
    ▼    ▼         ▼       ▼
  原样   广播给    转发给   返回
  返回   所有人    房间成员  pong
```

### 模块依赖关系

```
server.py ──► connection/manager.py
         ──► models/message.py
         ──► core/config.py
core/config.py ──► (Pydantic Settings, .env)
core/logger.py ──► (Python logging)
__main__.py ──► server.py, core/config.py (CLI 入口)
```

## 快速开始

### 环境要求

| 项目     | 要求                                        |
| ------ | ----------------------------------------- |
| Python | >= 3.11                                   |
| 包管理器   | [uv](https://docs.astral.sh/uv/)（推荐）或 pip |
| 操作系统   | Windows / Linux / macOS                   |

### 1. 克隆项目

```bash
git clone https://gitee.com/yeyushilai/x-websocket.git
cd x-websocket
```

### 2. 安装依赖

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
# Linux / macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装项目依赖
uv pip install -e .

# 安装开发依赖（可选）
uv pip install -e ".[dev]"
```

### 3. 配置环境变量（可选）

```bash
cp .env.example .env
```

所有配置项均有默认值，无需修改即可运行。参见 [.env.example](.env.example)。

### 4. 启动服务器

```bash
# 默认启动（0.0.0.0:8765）
x-websocket serve

# 自定义端口
x-websocket serve --port 9000

# 开发模式（热重载）
x-websocket serve --reload
```

### 5. 运行示例

打开新终端，运行示例客户端：

```bash
# 示例 1：Echo 回显（最简单，推荐首先运行）
python examples/01_echo.py

# 示例 2：广播（需要开两个终端）
python examples/02_broadcast.py

# 示例 3：房间聊天（需要开两个终端）
python examples/03_room_chat.py

# 示例 4：心跳检测
python examples/04_heartbeat.py
```

### 常用命令

| 命令                   | 说明                |
| -------------------- | ----------------- |
| `x-websocket serve`  | 启动 WebSocket 服务器  |
| `x-websocket config` | 查看当前配置            |
| `pytest tests/`      | 运行测试              |
| `ruff check src/`    | 代码检查              |
| `black src/`         | 代码格式化             |

## Docker 部署

### 构建镜像

```bash
docker build -t x-websocket .
```

### 运行容器

```bash
docker run -d --name x-websocket -p 8765:8765 x-websocket
```

### 使用 Docker Compose

```bash
# 启动（后台）
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

配置通过 `docker-compose.yml` 中的 `environment` 或挂载 `.env` 文件实现。

## 示例说明

### 示例 1 — Echo（回显）

最基础的 WebSocket 通信模式。客户端发送消息，服务器原样返回。

```json
// 客户端发送
{"type": "echo", "content": "你好"}
// 服务器返回（原样）
{"type": "echo", "content": "你好", "timestamp": 1726000000.0}
```

### 示例 2 — Broadcast（广播）

一对多通信。客户端发送广播消息，服务器转发给所有已连接客户端。

```json
// 客户端发送
{"type": "broadcast", "content": "大家好"}
// 服务器转发给所有人（含 sender 字段标识发送者）
{"type": "broadcast", "content": "大家好", "sender": "a1b2c3d4", "timestamp": 1726000000.0}
```

### 示例 3 — Room Chat（房间聊天）

房间机制。客户端加入指定房间后，消息仅转发给同一房间内的其他成员（不回显给发送者）。

```json
// 客户端发送
{"type": "chat", "content": "房间里的消息", "room_id": "demo_room"}
// 服务器转发给同房间其他成员
{"type": "chat", "content": "房间里的消息", "room_id": "demo_room", "sender": "a1b2c3d4", "timestamp": 1726000000.0}
```

### 示例 4 — Heartbeat（心跳）

Ping/Pong 保活检测。客户端定期发送 Ping，服务器回复 Pong，用于检测连接存活和测量延迟。

```json
// 客户端发送
{"type": "ping", "seq": 1}
// 服务器返回
{"type": "pong", "timestamp": 1726000000.0}
```

## 技术栈

| 分类         | 技术                                                                                                     |
| ---------- | ------------------------------------------------------------------------------------------------------ |
| **Web 框架** | [FastAPI](https://fastapi.tiangolo.com/) — 高性能异步 Web 框架                                                  |
| **ASGI 服务器** | [Uvicorn](https://www.uvicorn.org/) — 基于 uvloop 的 ASGI 服务器                                               |
| **WebSocket** | [websockets](https://websockets.readthedocs.io/) — Python WebSocket 库                                  |
| **数据校验**   | [Pydantic](https://docs.pydantic.dev/) / [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| **CLI 工具** | [Click](https://click.palletsprojects.com/) + [Rich](https://rich.readthedocs.io/)                      |
| **包管理**    | [uv](https://docs.astral.sh/uv/) — 高性能 Python 包管理器                                                       |
| **代码质量**   | [Ruff](https://docs.astral.sh/ruff/) / [Black](https://black.readthedocs.io/) / [mypy](https://mypy.readthedocs.io/) |

## 配置说明

所有配置项均有默认值，可通过环境变量或 `.env` 文件覆盖：

| 变量名        | 说明    | 默认值       |
| ---------- | ----- | --------- |
| `HOST`     | 监听地址  | `0.0.0.0` |
| `PORT`     | 监听端口  | `8765`    |
| `DEBUG`    | 调试模式  | `true`    |
| `LOG_LEVEL` | 日志级别  | `INFO`    |

## 开发指南

### 编码规范

| 项目 | 规范 |
|---|---|
| **语言** | 文档字符串、注释、日志、CLI 帮助使用**简体中文**；代码标识符使用英文 |
| **导入** | `src/` 内使用相对导入 |
| **文档字符串** | Google 风格，包含 `Args:` / `Returns:` / `Raises:` |
| **类型标注** | 所有函数签名均需类型注解 |
| **日志** | 使用 loguru，从 `src.core.logger` 导入 `logger` |
| **命名** | 类名 PascalCase，函数名 snake_case，私有方法 `_前缀` |
| **行宽** | 88（ruff + black） |

### 运行测试

```bash
uv pip install -e ".[dev]"
pytest tests/
pytest tests/ --cov=src --cov-report=html
```

### 代码检查

```bash
ruff check src/       # lint
black src/            # 格式化
isort src/            # import 排序
mypy src/             # 类型检查
```

## 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

## 参考资料

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [WebSocket 协议 (RFC 6455)](https://datatracker.ietf.org/doc/html/rfc6455)
- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [uv 官方文档](https://docs.astral.sh/uv/)

## 联系方式

- **作者**：John Young（夜雨诗来）
- **邮箱**：[john.young@foxmail.com](mailto:john.young@foxmail.com)
- **Gitee**：[https://gitee.com/yeyushilai](https://gitee.com/yeyushilai)
- **GitHub**：[https://github.com/yeyushilai](https://github.com/yeyushilai)
