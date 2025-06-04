#!/bin/bash

# FIST Content Moderation API - 启动脚本

set -e

echo "🚀 FIST Content Moderation API 启动脚本"
echo "========================================"

# 检查是否存在 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在，正在复制示例文件..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑配置后重新运行"
    echo "📝 主要配置项："
    echo "   - SECRET_KEY: 设置安全密钥"
    echo "   - ADMIN_PASSWORD: 设置管理员密码"
    echo "   - DATABASE_URL: 配置数据库连接"
    echo "   - AI_API_KEY: 配置AI服务密钥"
    exit 1
fi

echo "✅ 环境配置文件检查通过"

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python 版本检查通过: $(python3 --version)"
else
    echo "❌ Python 版本过低: $(python3 --version)"
    echo "   需要 Python 3.8 或更高版本"
    exit 1
fi

# 检查是否安装了依赖
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "📦 安装依赖..."
    if command -v uv &> /dev/null; then
        uv pip install -e .
    else
        pip install -e .
    fi
else
    echo "✅ 虚拟环境已存在"
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source .venv/bin/activate
    fi
fi

# 运行部署检查
echo "🔍 运行部署检查..."
python deploy_check.py

if [ $? -ne 0 ]; then
    echo "❌ 部署检查失败，请解决问题后重试"
    exit 1
fi

echo "✅ 部署检查通过"

# 启动服务
echo "🚀 启动 FIST API 服务..."
echo "📍 服务地址: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo "📖 ReDoc 文档: http://localhost:8000/redoc"
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================"

# 启动 uvicorn 服务器
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
