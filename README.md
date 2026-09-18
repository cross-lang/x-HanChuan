# x-HanChuan

`x-HanChuan` 是一个基于 WebSocket 协议的实时通信服务，支持回显、广播、房间聊天、心跳保活等核心消息模式。适用于即时通讯、实时通知、协同编辑、在线协作等需要低延迟双向通信的业务场景。

## 核心特征

- **多模式消息路由** — Echo 回显、Broadcast 广播、Room Chat 房间聊天、Ping/Pong 心跳保活
- **Pydantic v2 数据校验** — 所有消息模型强类型校验，入站/出站消息结构化保障
- **连接生命周期管理** — 自动注册/注销、房间机制、空房间自动清理
- **结构化日志** — loguru 双模式输出（JSON 生产环境 / 彩色控制台开发环境），日志轮转与自动清理
- **配置驱动** — Pydantic Settings 统一配置，支持 `.env` 文件与环境变量，类型安全
- **CLI 工具** — 内置 `x-HanChuan` 命令行工具，一键启动服务
- **容器化部署** — Docker 多阶段构建、tini PID 1、非 root 运行、Docker Compose 编排
- **依赖锁定** — uv 包管理 + `uv.lock` 锁定文件，保证环境一致性

## 项目结构

```
x-HanChuan/
├── src/                            # 源码根目录
│   ├── __init__.py                 # 包元数据与版本信息
│   ├── __main__.py                 # CLI 入口（Click 命令组）
│   ├── server.py                   # FastAPI 应用，WebSocket 端点与消息路由
│   ├── constants/                  # 常量与枚举
│   │   ├── constants.py            # 全局常量（APP_NAME / APP_VERSION 等）
│   │   ├── enums.py                # 业务枚举（MessageType / CommonStatus）
│   │   └── base.py                 # 可描述枚举基类
│   ├── connection/                 # 连接管理
│   │   └── manager.py              # WebSocket 连接管理器（注册/注销/广播/房间）
│   ├── core/                       # 核心基础设施
│   │   ├── config.py               # Pydantic Settings 配置类
│   │   └── logger.py               # loguru 日志（JSON / 彩色控制台）
│   └── models/                     # 数据模型
│       └── message.py              # Pydantic 消息模型（BaseMessage 继承体系）
├── examples/                       # 参考客户端实现
│   ├── 01_echo.py                  # Echo 回显
│   ├── 02_broadcast.py             # 广播
│   ├── 03_room_chat.py             # 房间聊天
│   └── 04_heartbeat.py             # 心跳检测
├── pyproject.toml                  # 项目配置与依赖声明
├── uv.lock                         # 依赖锁定文件
├── uv.toml                         # uv 包管理器配置
├── Dockerfile                      # Docker 多阶段构建
├── docker-compose.yml              # Docker Compose 编排
├── config.yaml.example             # YAML 配置参考
├── .env.example                    # 环境变量参考
├── CHANGELOG.md                    # 版本变更日志
├── LICENSE                         # MIT 许可证
├── README.md                       # 中文文档
└── README.en.md                    # 英文文档
```

## 系统架构

### 分层架构

```mermaid
graph TB
    subgraph 客户端层
        C1[WebSocket Client]
        C2[CLI 客户端]
        C3[浏览器]
    end

    subgraph 接入层
        GW[FastAPI + WebSocket /ws 端点]
    end

    subgraph 消息处理层
        ECHO[Echo 回显]
        BROADCAST[Broadcast 广播]
        CHAT[Chat 房间聊天]
        PING[Ping/Pong 心跳]
    end

    subgraph 连接管理层
        CM[ConnectionManager<br/>连接注册/注销/广播/房间]
    end

    subgraph 基础设施层
        CFG[Config<br/>Pydantic Settings]
        LOG[Logger<br/>loguru]
        CLI_MOD[CLI<br/>Click + Rich]
    end

    C1 --> GW
    C2 --> GW
    C3 --> GW
    GW --> ECHO
    GW --> BROADCAST
    GW --> CHAT
    GW --> PING
    ECHO --> CM
    BROADCAST --> CM
    CHAT --> CM
    CM --> CFG
    CM --> LOG
    CLI_MOD --> CFG
    CLI_MOD --> LOG
```

### 消息处理流程

```mermaid
flowchart TD
    A[客户端发送 JSON 消息] --> B{解析 JSON}
    B -->|无效| C[返回 ErrorMessage]
    B -->|有效| D{校验 BaseMessage}
    D -->|校验失败| C
    D -->|校验成功| E{type 字段路由}

    E -->|echo| F[_handle_echo<br/>原样返回]
    E -->|broadcast| G[_handle_broadcast<br/>广播给所有人]
    E -->|chat| H[_handle_chat<br/>转发给房间成员]
    E -->|ping| I[_handle_ping<br/>返回 pong]
    E -->|未知类型| C

    G --> J[ConnectionManager.broadcast]
    H --> K[ConnectionManager.broadcast_to_room]
```

## 快速开始

### 环境要求

| 项目 | 要求 |
|------|------|
| Python | >= 3.11 |
| 包管理器 | [uv](https://docs.astral.sh/uv/) |

**操作系统支持：**

| 平台 | 安装 Python | 安装 uv |
|------|------------|---------|
| **Windows** | [python.org](https://www.python.org/downloads/) 或 `winget install Python.Python.3.11` | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| **Linux** | `sudo apt install python3.11` (Debian/Ubuntu) 或系统包管理器 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **macOS** | `brew install python@3.11` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

### 1. 克隆项目

```bash
# Gitee
git clone https://gitee.com/yeyushilai/x-HanChuan.git
cd x-HanChuan

# GitHub
git clone https://github.com/yeyushilai/x-HanChuan.git
cd x-HanChuan
```

### 2. 同步依赖

```bash
# 同步依赖（自动创建 .venv 并安装所有包）
uv sync

# 如需开发依赖（pytest / ruff / mypy 等）
uv sync --dev
```

### 3. 环境配置

```bash
cp .env.example .env
```

所有配置项均有默认值，无需修改即可运行。完整参数说明：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `HOST` | 服务器监听地址 | `0.0.0.0` |
| `PORT` | 服务器监听端口 | `8765` |
| `DEBUG` | 调试模式 | `true` |
| `LOG_LEVEL` | 日志级别（DEBUG / INFO / WARNING / ERROR / CRITICAL） | `INFO` |
| `LOGGING_FORMAT` | 日志格式（`json` 生产环境 / `console` 开发环境） | `console` |

### 4. 启动服务

#### 本地开发（热重载）

```bash
uv run x-HanChuan serve --reload
```

#### 生产环境

```bash
uv run x-HanChuan serve --host 0.0.0.0 --port 8765
```

#### Docker 容器部署

```bash
# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

### 5. 常用工程命令

```bash
# 运行测试
uv run pytest
uv run pytest --cov=src --cov-report=html

# 代码格式化
uv run black src/
uv run isort src/

# 静态检查
uv run ruff check src/
uv run mypy src/

# 依赖漏洞扫描
uv run pip-audit

# 查看当前配置
uv run x-HanChuan config
```

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
uv run pytest
uv run pytest --cov=src --cov-report=html
```

### 代码检查

```bash
uv run ruff check src/       # lint
uv run black src/            # 格式化
uv run isort src/            # import 排序
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
