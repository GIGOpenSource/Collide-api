# ==========================================
# Collide User Service Dockerfile
# 基于Python 3.11的轻量级镜像
# ==========================================

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "start.py"]

# ==========================================
# 构建和运行说明：
# 
# 1. 构建镜像：
#    docker build -t collide-api-service:latest .
#
# 2. 运行容器：
#    docker run -d \
#      --name collide-user-service \
#      -p 8000:8000 \
#      -e DATABASE_URL="mysql+pymysql://root:password@host.docker.internal:3306/collide" \
#      -e NACOS_SERVER="host.docker.internal:8848" \
#      collide-user-service:latest
#
# 3. 查看日志：
#    docker logs -f collide-user-service
#
# 4. 进入容器：
#    docker exec -it collide-user-service bash
# ==========================================