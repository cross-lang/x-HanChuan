# x-HanChuan

[English](README.en.md) | [中文](README.md)

#### Description
**x-HanChuan** is a WebSocket-based LLM (Large Language Model) demonstration application that supports streaming conversations and chat functionality across multiple model providers (OpenAI, Kimi, DeepSeek, etc.). Built with FastAPI, it provides complete WebSocket communication, JWT authentication, and extensible LLM interfaces.

#### Features
- 🌐 **WebSocket Real-time Communication**: Bidirectional real-time message transmission
- 🔐 **JWT Authentication**: Secure user authentication and authorization
- 🤖 **Multi-model Support**: OpenAI, Kimi, DeepSeek, Mock, Local LLM
- 🔌 **Extensible Architecture**: Easy to add new LLM providers
- 📊 **Connection Management**: Room broadcasting, personal messages, and connection status management
- ⚡ **Streaming Responses**: LLM streaming generation with real-time display
- 🛠️ **Command-line Tool**: Rich CLI commands for server management and testing

#### Software Architecture
```
x-HanChuan/
├── src/x_HanChuan/
│   ├── __init__.py          # Package metadata
│   ├── __main__.py          # CLI entry point
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API routes and message handlers
│   ├── auth/                # Authentication module
│   │   └── jwt_auth.py      # JWT authentication service
│   ├── connection/          # Connection management
│   │   └── manager.py       # WebSocket connection manager
│   ├── core/                # Core functionality modules
│   │   ├── __init__.py      # Package initialization
│   │   ├── config.py        # Configuration management (Pydantic Settings)
│   │   └── logger.py        # Logging configuration
│   ├── handlers/            # Message handlers
│   │   ├── base.py          # Base handler
│   │   ├── chat.py          # Chat message handler
│   │   ├── status.py        # Status query handler
│   │   └── stream.py        # Streaming message handler
│   ├── llm/                 # LLM provider interfaces
│   │   ├── base.py          # LLM abstract base class and factory
│   │   ├── openai.py        # OpenAI client
│   │   ├── kimi.py          # Kimi client
│   │   ├── deepseek.py      # DeepSeek client
│   │   ├── mock.py          # Mock LLM (for testing)
│   │   └── local.py         # Local LLM support
│   └── schemas/             # Data model layer (Schemas)
│       └── message.py       # Message data models
├── examples/                # Example code
│   └── basic_client.py      # Basic WebSocket client example
├── tests/                   # Test directory
├── pyproject.toml           # Project configuration and dependencies
├── uv.lock                  # Dependency lock file
├── .env.example             # Environment variables example
└── README.md                # Project documentation
```

#### Installation

##### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

##### 1. Clone the repository
```bash
git clone https://gitee.com/your-username/x-HanChuan.git
cd x-HanChuan
```

##### 2. Install dependencies
```bash
# Sync dependencies (auto-creates .venv and installs all packages)
uv sync

# With development dependencies (pytest / ruff / mypy)
uv sync --dev
```

##### 3. Configure environment variables
```bash
# Copy environment variables example file
cp .env.example .env

# Edit .env file, configure necessary API keys
# At minimum, set JWT_SECRET and at least one LLM provider API key
```

##### 4. Generate JWT token
```bash
# Generate authentication token for user
x-HanChuan token test_user_001
```

#### Usage

##### Start the server
```bash
# Default startup (host: 0.0.0.0, port: 8000)
uv run x-HanChuan serve

# Custom host and port
uv run x-HanChuan serve --host 127.0.0.1 --port 8000

# Enable hot reload (development mode)
uv run x-HanChuan serve --reload
```

##### View current configuration
```bash
uv run x-HanChuan config
```

##### Health check
```bash
x-HanChuan health
```

##### WebSocket connection example
After starting the server, connect to `ws://localhost:8000/api/v1/ws` via a WebSocket client. Connection flow:

1. **Establish connection**: Connect to the WebSocket endpoint
2. **Send authentication message**: Send authentication message with JWT token immediately after connection
   ```json
   {"token": "your_jwt_token_here"}
   ```
3. **Receive connection confirmation**: Server returns connection success message
4. **Send messages**: Three message types supported:
   - `chat`: Chat messages
   - `stream`: Streaming generation requests
   - `status`: Status queries

##### Message formats
###### Streaming request
```json
{
  "type": "stream",
  "prompt": "Please introduce the WebSocket protocol",
  "model": "openai"  // Optional, defaults to configured provider
}
```

###### Chat message
```json
{
  "type": "chat",
  "content": "Hello, this is a test message",
  "room_id": "room_001"  // Optional, for room broadcasting
}
```

###### Status query
```json
{
  "type": "status",
  "task_id": "task_123",
  "action": "query"
}
```

##### Run example client
```bash
# Ensure server is running
python examples/basic_client.py
```

#### Configuration

##### Environment variables
Complete configuration reference in `.env.example` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `true` |
| `JWT_SECRET` | JWT secret key | **Required** |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `LLM_PROVIDER` | Default LLM provider | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `KIMI_API_KEY` | Kimi API key | - |
| `DEEPSEEK_API_KEY` | DeepSeek API key | - |

##### Supported LLM providers
- `openai`: OpenAI compatible API (including Azure OpenAI)
- `kimi`: Kimi (Moonshot) API
- `deepseek`: DeepSeek API
- `mock`: Mock LLM, for testing and development
- `local`: Locally deployed LLM (requires transformers)

#### API Documentation
After starting the server, access the following URLs for API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### Development Guide

##### Adding new LLM providers
1. Create a new client class in `src/x_HanChuan/llm/` directory, inheriting from `BaseLLM`
2. Implement `generate_stream()`, `chat()`, and `get_status()` methods
3. Register the new provider in the `LLMFactory` class
4. Add corresponding configuration fields in the `Settings` class

##### Running tests
```bash
# Run tests
uv run pytest

# Run specific test file
uv run x-HanChuan serve
```

#### Contributing

1.  **Fork the repository**
2.  **Create feature branch**
    ```bash
    git checkout -b feat/your-feature-name
    ```
3.  **Commit your changes**
    ```bash
    git commit -m "feat: add some feature"
    ```
4.  **Push to the branch**
    ```bash
    git push origin feat/your-feature-name
    ```
5.  **Create a Pull Request**

#### License
This project is open source under the MIT License. See the [LICENSE](LICENSE) file for details.

#### Issue Reporting
If you encounter any issues, please submit an Issue or contact via:
- GitHub Issues: [Project URL](https://github.com/your-username/x-HanChuan/issues)
- Email: john.young@foxmail.com

---
*Thank you for using x-HanChuan! If you find this project useful, please give it a Star ⭐️*
