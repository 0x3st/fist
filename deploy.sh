#!/bin/bash

# FIST Content Moderation API - 生产部署管理脚本
# 集成了启动、重启、配置管理、API密钥设置等功能

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

show_help() {
    cat << EOF
🐳 FIST 生产部署管理器

用法: $0 [命令] [选项]

命令:
  start          启动服务
  restart        重启服务 (完全重建)
  stop           停止服务
  status         查看服务状态
  logs           查看服务日志
  setup-api      设置API密钥
  init [env]     初始化环境配置 (dev|prod|test)
  backup         备份当前配置
  validate       验证配置
  help           显示此帮助信息

示例:
  $0 start               # 启动服务
  $0 restart             # 重启服务
  $0 setup-api           # 设置API密钥
  $0 init prod           # 初始化生产环境配置
  $0 logs                # 查看日志

环境说明:
  dev    - 开发环境 (启用调试，使用SQLite，禁用缓存)
  prod   - 生产环境 (优化性能，使用PostgreSQL，启用所有功能)
  test   - 测试环境 (最小配置，快速启动)
EOF
}

check_docker() {
    # 检查 Docker 是否安装
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker 未安装，请先安装 Docker"
        echo "   访问: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # 检查 Docker Compose 是否安装
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
        echo "   访问: https://docs.docker.com/compose/install/"
        exit 1
    fi

    # 确定使用哪个 Docker Compose 命令
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi

    echo "✅ Docker 环境检查通过"
}

start_services() {
    echo "🐳 FIST Content Moderation API - 启动服务"
    echo "=============================================="
    
    check_docker

    # 检查是否有运行中的容器
    if $DOCKER_COMPOSE ps | grep -q "Up"; then
        echo "⚠️  检测到运行中的容器"
        read -p "是否停止现有容器并重新启动？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🛑 停止现有容器..."
            $DOCKER_COMPOSE down
        else
            echo "❌ 取消启动"
            exit 1
        fi
    fi

    # 构建并启动服务
    echo "🔨 构建 Docker 镜像..."
    $DOCKER_COMPOSE build

    echo "🚀 启动服务..."
    $DOCKER_COMPOSE up -d

    # 等待服务启动
    echo "⏳ 等待服务启动..."
    sleep 10

    # 检查服务状态
    echo "📊 检查服务状态..."
    $DOCKER_COMPOSE ps

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
        echo "   - 查看日志: $0 logs"
        echo "   - 停止服务: $0 stop"
        echo "   - 重启服务: $0 restart"
        echo ""
        echo "🔧 配置提醒:"
        echo "   - 请使用 '$0 setup-api' 配置API密钥"
        echo "   - 请使用 '$0 init prod' 初始化生产环境"
    else
        echo "❌ API 服务启动失败"
        echo "📋 查看日志:"
        $DOCKER_COMPOSE logs fist-api
        exit 1
    fi

    echo "=============================================="
    echo "🎉 FIST API 部署完成！"
}

restart_services() {
    echo "🔄 FIST Docker 重启服务"
    echo "=========================="
    
    check_docker

    # Stop and remove containers, networks, and volumes
    echo "停止并移除容器..."
    $DOCKER_COMPOSE down -v

    # Remove any orphaned containers
    echo "移除孤立容器..."
    $DOCKER_COMPOSE down --remove-orphans

    # Pull latest images
    echo "拉取最新镜像..."
    $DOCKER_COMPOSE pull

    # Build the application image
    echo "构建应用镜像..."
    $DOCKER_COMPOSE build --no-cache

    # Start the services
    echo "启动服务..."
    $DOCKER_COMPOSE up -d

    # Wait a moment for services to start
    echo "等待服务启动..."
    sleep 10

    # Check service status
    echo "检查服务状态..."
    $DOCKER_COMPOSE ps

    # Show logs for the API service
    echo "显示API服务日志..."
    $DOCKER_COMPOSE logs fist-api

    echo ""
    echo "Docker 重启完成！"
    echo "API 地址: http://localhost:8000"
    echo "API 文档: http://localhost:8000/docs"
}

stop_services() {
    echo "🛑 停止 FIST 服务"
    check_docker
    $DOCKER_COMPOSE down
    echo "✅ 服务已停止"
}

show_status() {
    echo "📊 FIST 服务状态"
    check_docker
    $DOCKER_COMPOSE ps
}

show_logs() {
    echo "📋 FIST 服务日志"
    check_docker
    $DOCKER_COMPOSE logs -f fist-api
}

setup_api_key() {
    echo "🔑 FIST API Key 设置向导"
    echo "======================="

    # 检查是否已有配置
    if [ -f .env.local ]; then
        echo "⚠️  检测到现有的 .env.local 文件"
        read -p "是否要覆盖现有配置？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ 取消设置"
            return 0
        fi
    fi

    echo "📝 请选择您要使用的AI服务："
    echo "1) OpenAI (ChatGPT)"
    echo "2) Anthropic (Claude)"
    echo "3) 阿里云通义千问"
    echo "4) 百度文心一言"
    echo "5) 腾讯混元"
    echo "6) 自定义"

    read -p "请选择 (1-6): " choice

    case $choice in
        1)
            AI_SERVICE="OpenAI"
            AI_API_URL="https://api.openai.com/v1"
            echo "📋 请输入您的 OpenAI API Key (sk-开头):"
            ;;
        2)
            AI_SERVICE="Anthropic"
            AI_API_URL="https://api.anthropic.com/v1"
            echo "📋 请输入您的 Anthropic API Key (sk-ant-开头):"
            ;;
        3)
            AI_SERVICE="阿里云通义千问"
            AI_API_URL="https://dashscope.aliyuncs.com/api/v1"
            echo "📋 请输入您的阿里云 API Key:"
            ;;
        4)
            AI_SERVICE="百度文心一言"
            AI_API_URL="https://aip.baidubce.com/rpc/2.0/ai_custom/v1"
            echo "📋 请输入您的百度 API Key:"
            ;;
        5)
            AI_SERVICE="腾讯混元"
            AI_API_URL="https://hunyuan.tencentcloudapi.com"
            echo "📋 请输入您的腾讯云 API Key:"
            ;;
        6)
            echo "📋 请输入自定义 API URL:"
            read -p "API URL: " AI_API_URL
            echo "📋 请输入您的 API Key:"
            AI_SERVICE="自定义"
            ;;
        *)
            echo "❌ 无效选择"
            return 1
            ;;
    esac

    # 读取API Key（隐藏输入）
    read -s -p "API Key: " AI_API_KEY
    echo

    if [ -z "$AI_API_KEY" ]; then
        echo "❌ API Key 不能为空"
        return 1
    fi

    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    ADMIN_PASSWORD=$(openssl rand -base64 16 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(16))")

    # 创建 .env.local 文件
    cat > .env.local << EOF
# FIST 本地环境变量配置
# 由 deploy.sh 自动生成于 $(date)

# AI 服务配置 ($AI_SERVICE)
AI_API_KEY=$AI_API_KEY
AI_API_URL=$AI_API_URL

# 安全配置（自动生成）
SECRET_KEY=$SECRET_KEY
ADMIN_PASSWORD=$ADMIN_PASSWORD

# 功能开关
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_TOPIC_EXTRACTION=true
ENABLE_TEXT_ANALYSIS=true
ENABLE_MULTILINGUAL=true
ENABLE_CACHING=true

# 性能配置
MAX_CONTENT_LENGTH=10000
MAX_BATCH_SIZE=1000
CACHE_TTL=3600
WORKER_THREADS=4
EOF

    echo "✅ 配置文件已创建: .env.local"
    echo ""
    echo "📋 配置摘要:"
    echo "   AI 服务: $AI_SERVICE"
    echo "   API URL: $AI_API_URL"
    echo "   API Key: ${AI_API_KEY:0:8}... (已隐藏)"
    echo "   管理员密码: $ADMIN_PASSWORD"
    echo ""
    echo "🔒 安全提醒:"
    echo "   - .env.local 文件包含敏感信息，已自动添加到 .gitignore"
    echo "   - 请妥善保管您的 API Key 和管理员密码"
    echo "   - 生产环境请修改默认密码"
    echo ""
    echo "🚀 下一步:"
    echo "   1. 启动服务: $0 start"
    echo "   2. 检查健康状态: curl http://localhost:8000/"
    echo "   3. 访问API文档: http://localhost:8000/docs"
    echo "   4. 使用管理员密码登录: $ADMIN_PASSWORD"
}

init_config() {
    local env=${1:-dev}

    echo "🚀 初始化 $env 环境配置..."

    case $env in
        dev)
            cat > docker-compose.override.yml << 'EOF'
version: '3.8'
services:
  fist-api:
    environment:
      - DEBUG=true
      - ENABLE_CACHING=false
      - ENABLE_MULTILINGUAL=false
      - SECRET_KEY=dev-secret-key-change-me
      - ADMIN_PASSWORD=dev-admin-password
    ports:
      - "8001:8000"
    volumes:
      - ./logs:/app/logs
      - ./dev-data:/app/data

  db:
    ports:
      - "5433:5432"
    environment:
      POSTGRES_DB: fist_dev_db
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password

  redis:
    ports:
      - "6380:6379"
    command: redis-server --appendonly yes --maxmemory 256mb
EOF
            ;;
        prod)
            cat > docker-compose.override.yml << 'EOF'
version: '3.8'
services:
  fist-api:
    environment:
      - DEBUG=false
      - ENABLE_CACHING=true
      - ENABLE_MULTILINGUAL=true
      - ENABLE_SENTIMENT_ANALYSIS=true
      - ENABLE_TOPIC_EXTRACTION=true
      - ENABLE_TEXT_ANALYSIS=true
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  db:
    # 生产环境不暴露端口
    ports: []

  redis:
    # 生产环境不暴露端口
    ports: []
    command: redis-server --appendonly yes --maxmemory 1gb
EOF
            ;;
        test)
            cat > docker-compose.override.yml << 'EOF'
version: '3.8'
services:
  fist-api:
    environment:
      - DEBUG=true
      - ENABLE_CACHING=false
      - ENABLE_SENTIMENT_ANALYSIS=false
      - ENABLE_TOPIC_EXTRACTION=false
      - ENABLE_TEXT_ANALYSIS=true
      - ENABLE_MULTILINGUAL=false
      - SECRET_KEY=test-secret-key
      - ADMIN_PASSWORD=test-admin-password
    ports:
      - "8002:8000"

  # 测试环境使用内存数据库
  db:
    environment:
      POSTGRES_DB: fist_test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    tmpfs:
      - /var/lib/postgresql/data

  redis:
    command: redis-server --save ""
    tmpfs:
      - /data
EOF
            ;;
        *)
            echo "❌ 未知环境: $env"
            echo "支持的环境: dev, prod, test"
            return 1
            ;;
    esac

    echo "✅ $env 环境配置已创建"
    echo "📝 配置文件: docker-compose.override.yml"
    echo "🔧 验证配置: $0 validate"
}

backup_config() {
    echo "💾 备份当前配置..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="config_backups"

    mkdir -p "$backup_dir"

    if [ -f docker-compose.override.yml ]; then
        cp docker-compose.override.yml "$backup_dir/docker-compose.override.yml.$timestamp"
        echo "✅ 已备份 override 配置到: $backup_dir/docker-compose.override.yml.$timestamp"
    fi

    if [ -f .env.local ]; then
        cp .env.local "$backup_dir/.env.local.$timestamp"
        echo "✅ 已备份环境变量到: $backup_dir/.env.local.$timestamp"
    fi

    echo "📋 备份列表:"
    ls -la "$backup_dir/" | tail -5
}

validate_config() {
    echo "🔍 验证配置..."

    check_docker

    # 检查 docker-compose 配置
    if $DOCKER_COMPOSE config > /dev/null 2>&1; then
        echo "✅ Docker Compose 配置有效"
    else
        echo "❌ Docker Compose 配置无效"
        echo "📋 错误详情:"
        $DOCKER_COMPOSE config
        return 1
    fi

    # 检查端口冲突
    echo "🔍 检查端口占用..."
    local ports=(8000 8001 8002 5432 5433 6379 6380)
    for port in "${ports[@]}"; do
        if lsof -i :$port > /dev/null 2>&1; then
            echo "⚠️  端口 $port 已被占用"
        fi
    done

    echo "✅ 配置验证完成"
}

# 主逻辑
case "${1:-help}" in
    start)
        start_services
        ;;
    restart)
        restart_services
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    setup-api)
        setup_api_key
        ;;
    init)
        init_config "$2"
        ;;
    backup)
        backup_config
        ;;
    validate)
        validate_config
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo "使用 '$0 help' 查看帮助"
        exit 1
        ;;
esac
