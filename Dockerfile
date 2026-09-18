# ============================================================
# x-websocket Dockerfile
# ============================================================
# 多阶段构建：builder 安装依赖，runtime 仅复制产物
# ============================================================

# ---- 构建阶段 ----
FROM python:3.11-slim AS builder

# 安装 uv（高速包管理器）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 先复制依赖声明，利用 Docker 缓存层
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# 安装生产依赖（不装 dev 依赖）
RUN uv pip install --system --no-cache -e .

# ---- 运行阶段 ----
FROM python:3.11-slim AS runtime

# 设置国内镜像源（可选，按需取消注释）
# RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制 Python 包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

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
ENV HOST=0.0.0.0
ENV PORT=8765
ENV LOG_LEVEL=INFO
ENV LOGGING_FORMAT=json

EXPOSE 8765

# 使用 tini 作为 PID 1，正确处理信号
ENTRYPOINT ["tini", "--"]

# 启动命令
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8765"]
