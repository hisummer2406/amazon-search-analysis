# Dockerfile
FROM registry.cn-beijing.aliyuncs.com/ruanjinggang/python:3.10-slim

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 设置系统依赖
RUN echo "deb http://mirrors.aliyun.com/debian bookworm main non-free non-free-firmware\n\
deb http://mirrors.aliyun.com/debian bookworm-updates main non-free non-free-firmware\n\
deb http://mirrors.aliyun.com/debian-security bookworm-security main non-free non-free-firmware" > /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p uploads/daily uploads/weekly logs static

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV OMP_NUM_THREADS=4
ENV MKL_NUM_THREADS=4
ENV OPENBLAS_NUM_THREADS=4

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]