#!/bin/bash

# FIST 配置管理脚本
# 用于管理不同环境的Docker配置

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

show_help() {
    cat << EOF
🔧 FIST 配置管理器

用法: $0 [命令] [选项]

命令:
  init [env]     初始化环境配置 (dev|prod|test)
  switch [env]   切换到指定环境
  backup         备份当前配置
  restore        恢复备份配置
  validate       验证当前配置
  status         显示当前配置状态
  help           显示此帮助信息

示例:
  $0 init dev              # 初始化开发环境配置
  $0 switch prod           # 切换到生产环境
  $0 backup               # 备份当前配置
  $0 validate             # 验证配置有效性

环境说明:
  dev    - 开发环境 (启用调试，使用SQLite，禁用缓存)
  prod   - 生产环境 (优化性能，使用PostgreSQL，启用所有功能)
  test   - 测试环境 (最小配置，快速启动)
EOF
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
            exit 1
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
    
    if [ -f .env ]; then
        cp .env "$backup_dir/.env.$timestamp"
        echo "✅ 已备份环境变量到: $backup_dir/.env.$timestamp"
    fi
    
    echo "📋 备份列表:"
    ls -la "$backup_dir/" | tail -5
}

validate_config() {
    echo "🔍 验证配置..."
    
    # 检查 docker-compose 配置
    if docker-compose config > /dev/null 2>&1; then
        echo "✅ Docker Compose 配置有效"
    else
        echo "❌ Docker Compose 配置无效"
        echo "📋 错误详情:"
        docker-compose config
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

show_status() {
    echo "📊 当前配置状态"
    echo "=================="
    
    if [ -f docker-compose.override.yml ]; then
        echo "✅ 存在 override 配置"
        echo "📋 当前环境变量:"
        grep -E "DEBUG|ENABLE_" docker-compose.override.yml | head -5 || true
    else
        echo "ℹ️  使用默认配置"
    fi
    
    echo ""
    echo "🐳 Docker 服务状态:"
    if docker-compose ps 2>/dev/null; then
        echo "✅ 服务正在运行"
    else
        echo "ℹ️  服务未启动"
    fi
}

# 主逻辑
case "${1:-help}" in
    init)
        init_config "$2"
        ;;
    switch)
        init_config "$2"
        ;;
    backup)
        backup_config
        ;;
    validate)
        validate_config
        ;;
    status)
        show_status
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
