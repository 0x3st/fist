#!/bin/bash

# FIST API Key 设置脚本

set -e

echo "🔑 FIST API Key 设置向导"
echo "======================="

# 检查是否已有配置
if [ -f .env.local ]; then
    echo "⚠️  检测到现有的 .env.local 文件"
    read -p "是否要覆盖现有配置？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消设置"
        exit 0
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
        exit 1
        ;;
esac

# 读取API Key（隐藏输入）
read -s -p "API Key: " AI_API_KEY
echo

if [ -z "$AI_API_KEY" ]; then
    echo "❌ API Key 不能为空"
    exit 1
fi

# 生成随机密钥
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_PASSWORD=$(openssl rand -base64 16 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(16))")

# 创建 .env.local 文件
cat > .env.local << EOF
# FIST 本地环境变量配置
# 由 setup-api-key.sh 自动生成于 $(date)

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
echo "   1. 启动服务: docker-compose up -d"
echo "   2. 检查健康状态: curl http://localhost:8001/health"
echo "   3. 访问API文档: http://localhost:8001/docs"
echo "   4. 使用管理员密码登录: $ADMIN_PASSWORD"
