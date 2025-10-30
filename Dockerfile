FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

RUN echo "deb http://mirrors.aliyun.com/debian/ trixie main non-free contrib" > /etc/apt/sources.list && \
    echo "deb-src http://mirrors.aliyun.com/debian/ trixie main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security/ trixie-security main" >> /etc/apt/sources.list && \
    echo "deb-src http://mirrors.aliyun.com/debian-security/ trixie-security main" >> /etc/apt/sources.list

# 安装系统依赖（含字体支持，解决PDF中文乱码）
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建静态文件目录（存放字体）
RUN mkdir -p /app/static/font
# 复制字体
COPY static/font/SimHei.ttf /app/static/font/

# 暴露端口（Flask默认5000）
EXPOSE 5000

# 启动命令（生产环境用gunicorn）
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]