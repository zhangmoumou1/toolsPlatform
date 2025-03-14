#!/bin/sh

# 执行重启操作
echo "--------------------------- Migrating Mysql Data ---------------------------"

# 获取所有服务容器的ID
containers=$(docker-compose ps -q)

# 遍历每个容器并执行数据迁移操作
for container in $containers; do

    # 检查容器是否包含所需环境（例如检查是否有alembic）
    has_alembic=$(docker exec "$container" sh -c 'which alembic || echo "Alembic not found"')

    if [ "$has_alembic" != "Alembic not found" ]; then
        # 在容器内执行数据迁移命令
        docker exec "$container" sh -c '
            if [ ! -d "alembic_pro" ]; then \
                alembic init alembic_pro; \
            else \
                echo "Alembic directory already exists, skipping initialization."; \
            fi && \
            alembic --config alembic.ini.pro revision --autogenerate -m "数据迁移" && \
            alembic --config alembic.ini.pro upgrade head
        '
    else
        echo "Skipping data migration for container $container as Alembic is not installed."
    fi
    # 执行重启操作
    echo "--------------------------- Restarting Services ---------------------------"
    docker-compose down
    # 清空日志文件
#    containers_new=$(docker-compose ps -q)
#    logPath=$(docker inspect --format='"{{.LogPath}}"' "containers_new")
#    docker exec -u root "containers_new" sh -c "truncate -s 0 $logPath"
done

docker-compose up -d

# 等待几秒钟确保服务已经完全重启（根据需要调整等待时间）
sleep 10

# 检查服务状态
echo "Checking service status:"
docker-compose ps
echo ""
# 查看最新启动日志
docker-compose logs