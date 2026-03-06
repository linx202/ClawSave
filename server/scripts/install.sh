#!/bin/bash
# ClawSave Server - Linux/Mac 一键部署

set -e

echo "=== ClawSave Server Installer ==="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# 创建 .env 文件
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env to set your credentials"
fi

# 初始化数据目录
echo "Initializing data directory..."
mkdir -p data/ClawSave/{_system,public,users}

# 复制初始配置
if [ ! -f data/ClawSave/_system/games_library.json ]; then
    cp -r config/init_data/* data/ClawSave/
fi

# 启动服务
echo "Starting WebDAV service..."
docker-compose up -d

echo "=== Installation Complete ==="
echo "WebDAV is running on port $(grep WEBDAV_PORT .env | cut -d= -f2 || echo 8080)"
