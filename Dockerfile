# 使用官方的 Python 镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装必要的依赖项
RUN apt update && \
    apt install -y libreoffice && \
    apt install -y pandoc && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# 将当前目录中的内容复制到容器中的工作目录
COPY . .

# 安装 Python 依赖项
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 6677

# 启动 FastAPI 应用程序
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6677"]