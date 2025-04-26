# Dockerfile
# 使用官方 Python 镜像作为基础
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装 supervisor 和 Python 依赖
# 先复制 requirements.txt 并安装，可以利用 Docker 的层缓存
# 注意：这里是从构建上下文的根目录复制
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends supervisor && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# 复制 supervisor 配置文件
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 复制所有应用程序代码到工作目录
# Dockerfile 和 supervisord.conf 已经在构建上下文的根目录，其他代码在 common/ 等子目录
COPY common ./common
COPY ai_service_1_tweet_processor.py .
COPY ai_service_2_web_processor.py .
COPY backend_1_crawler_mock.py .
COPY backend_2_url_processor.py .

# 设置默认的 RabbitMQ 主机环境变量 (可以在 docker run 时覆盖)
# 方便在 Docker Compose 或类似环境中使用服务名连接
ENV RABBITMQ_HOST=rabbitmq

# 容器启动时运行 supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 