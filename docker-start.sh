#!/bin/bash

# FIST Content Moderation API - Docker 快速启动脚本

set -e

echo "🐳 FIST Content Moderation API - Docker 部署"
echo "=============================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "   访问: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    echo "   访问: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 检查是否有运行中的容器
if docker-compose ps | grep -q "Up"; then
    echo "⚠️  检测到运行中的容器"
    read -p "是否停止现有容器并重新启动？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 停止现有容器..."
        docker-compose down
    else
        echo "❌ 取消启动"
        exit 1
    fi
fi

# 构建并启动服务
echo "🔨 构建 Docker 镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 测试API连接
echo "🔍 测试API连接..."
if curl -s -f http://localhost:8000/ > /dev/null; then
    echo "✅ API 服务启动成功！"
    echo ""
    echo "🌐 服务地址:"
    echo "   - API 主页: http://localhost:8000/"
    echo "   - API 文档: http://localhost:8000/docs"
    echo "   - ReDoc 文档: http://localhost:8000/redoc"
    echo ""
    echo "📝 管理命令:"
    echo "   - 查看日志: docker-compose logs -f fist-api"
    echo "   - 停止服务: docker-compose down"
    echo "   - 重启服务: docker-compose restart"
    echo ""
    echo "🔧 配置提醒:"
    echo "   - 请修改 docker-compose.yml 中的默认密码"
    echo "   - 请配置 AI_API_KEY 环境变量"
else
    echo "❌ API 服务启动失败"
    echo "📋 查看日志:"
    docker-compose logs fist-api
    exit 1
fi

echo "=============================================="
echo "🎉 FIST API 部署完成！"
