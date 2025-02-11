# 使用官方 FastAPI 基础镜像
FROM mirror.ccs.tencentyun.com/library/python:3.8
# 设置国内 pip 镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
# 设置工作目录
WORKDIR /app
# 复制项目文件到容器
COPY . /app
# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt
# 暴露端口（与 `pro.env` 里的 `SERVER_PORT` 对应）
EXPOSE 7777
# 启动 FastAPI
CMD ["sh", "-c", "uvicorn main:qms --host 0.0.0.0 --port ${SERVER_PORT} --reload --forwarded-allow-ips '*'"]