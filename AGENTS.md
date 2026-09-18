# AGENTS.md — x-websocket AI 代理指令

## 项目概述

基于 **FastAPI** 构建的 WebSocket LLM 实时交互应用，支持全双工流式对话，兼容 OpenAI / Kimi / DeepSeek / Mock / Local 多模型提供商。

- **Python**: >=3.11（目标 3.11）
- **构建工具**: Hatchling（`pyproject.toml`）
- **包管理器**: uv（推荐），兼容 pip
- **许可证**: MIT

## 构建与运行命令

```bash
# 环境搭建
uv venv && uv pip install -e ".[dev]"

# 启动服务
x-websocket serve                    # 默认 0.0.0.0:8765
x-websocket serve --port 9000 --reload

# CLI 工具
x-websocket token <user_id>          # 生成 JWT 令牌
x-websocket config                   # 查看当前配置

# 开发工具
ruff check src/                      # 代码检查
black src/                           # 代码格式化
isort src/                           # import 排序
mypy src/                            # 类型检查
pytest                               # 运行测试（tests/ 目录尚未创建）
```

## 架构

```
客户端 → FastAPI /ws 端点 → JWT 认证 → 消息路由
    → 处理器层（Chat / Stream / Status）
    → LLM 工厂 → 提供商（OpenAI / Kimi / DeepSeek / Mock / Local）
```

### 关键文件

| 文件 | 职责 |
|---|---|
| `src/server.py` | FastAPI 应用，WebSocket 端点，消息路由 |
| `src/__main__.py` | CLI 入口（Click 命令组） |
| `src/core/config.py` | 基于 `.env` 的 Pydantic Settings 配置 |
| `src/handlers/base.py` | 抽象 `BaseHandler` — 所有处理器的基类 |
| `src/handlers/{chat,stream,status}.py` | 具体消息处理器 |
| `src/llm/base.py` | `LLMFactory`、`BaseLLM` 抽象基类、`LLMProvider` 枚举、`LLMConfig` |
| `src/llm/openai.py` | OpenAI 客户端（Kimi/DeepSeek 继承此类） |
| `src/models/message.py` | 所有 Pydantic 消息模型 |
| `src/connection/manager.py` | WebSocket 连接与房间管理 |
| `src/auth/jwt_auth.py` | JWT 创建/验证/刷新 |
| `examples/basic_client.py` | WebSocket 客户端示例 |

### 设计模式

- **处理器模式**: `BaseHandler(ABC)` 定义 `handle(websocket, message, client_id)` — 通过继承添加新处理器
- **LLM 工厂模式**: `LLMFactory.create_llm(config)` / `create_from_settings(settings)` — 通过继承 `BaseLLM` 并注册到工厂来添加新提供商
- **Kimi 和 DeepSeek** 继承 `OpenAIClient`（OpenAI 兼容 API）— 仅覆盖 `base_url`
- **消息模型**: 统一定义在 `src/models/message.py`，Pydantic v2 `BaseModel`，通过 `MessageType` 枚举区分类型

## 编码规范

- **语言**: 所有文档字符串、注释、日志消息、CLI 帮助文本使用**简体中文**；变量名/代码标识符使用英文
- **导入**: `src/` 内使用相对导入（如 `from ..models.message import ...`）
- **文档字符串**: Google 风格，包含 `Args:`、`Returns:`、`Raises:` 段落，使用中文
- **类型标注**: 全面标注 — 所有函数签名均需类型注解，使用 `typing` 中的 `Dict`、`Optional`、`AsyncGenerator` 等
- **异步**: 所有处理器和 LLM 方法均为 `async`；流式输出使用 `AsyncGenerator`
- **日志**: 模块级 `logger = logging.getLogger(__name__)`，类级 `self.logger` 在 `__init__` 中初始化；日志消息使用中文
- **命名**: 类名 PascalCase，函数名 snake_case，私有方法 `_前缀`，枚举成员 UPPER_SNAKE_CASE
- **行宽**: 88（ruff + black）
- **错误处理**: 关闭连接前通过 WebSocket 发送结构化 `ErrorMessage`；LLM 客户端捕获 `APIError` 并回退

## 注意事项

1. **测试目录缺失** — `tests/` 在 README 中被引用但尚未创建，添加测试时需先创建该目录
2. **入口点不匹配** — `pyproject.toml` 声明 `src.__main__:main`，但 Click 命令组名为 `cli`，可能需要 `main = cli` 别名
3. **`asyncio.get_event_loop().time()`** — 在 Python 3.12+ 中已弃用，建议使用 `asyncio.get_running_loop().time()`
4. **全局单例** — `ConnectionManager`、处理器和 `LLMFactory` 在 `server.py` 中为模块级单例（非依赖注入）
5. **CORS 允许所有来源** — 开发环境 `allow_origins=["*"]`，生产环境需收紧
6. **需要 `.env` 文件** — `JWT_SECRET` 为必填项（无默认值），运行前请复制 `.env.example` 为 `.env`
7. **`LLMConfig` 是普通类** — 非 Pydantic 模型，与项目其他模型层不一致

## 环境配置

复制 `.env.example` 为 `.env`。关键变量：`JWT_SECRET`（必填）、`LLM_PROVIDER`（openai|kimi|deepseek|mock）、各提供商的 `*_API_KEY`/`*_BASE_URL`/`*_MODEL`。完整列表见 `.env.example`。

## 文档链接

- [README.md](README.md) — 完整中文文档，含架构图
- [README.en.md](README.en.md) — 英文版文档
- [.env.example](.env.example) — 所有环境变量及说明
