# ============================================================
# x-HanChuan Dockerfile
# ============================================================
# 多阶段构建：builder 安装依赖，runtime 仅复制产物
# ============================================================

# ---- 构建阶段 ----
FROM python:3.11-slim AS builder

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 先复制依赖声明，利用 Docker 缓存层
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src/ src/

# 安装生产依赖（不装 dev 依赖）
RUN uv sync --locked --no-dev --no-cache

# ---- 运行阶段 ----
FROM python:3.11-slim AS runtime

# 设置国内镜像源（可选，按需取消注释）
# RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制 Python 包（uv sync 安装到 .venv）
COPY --from=builder /app/.venv /app/.venv

# 将 .venv/bin 加入 PATH
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 复制源码和配置
COPY src/ src/
COPY .env.example .env.example

# 创建日志目录
RUN mkdir -p /app/logs

# 非 root 用户运行
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# 环境变量默认值
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000
ENV LOGGING_LEVEL=INFO
ENV LOGGING_FORMAT=json

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# 使用 tini 作为 PID 1，正确处理信号
ENTRYPOINT ["tini", "--"]

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
