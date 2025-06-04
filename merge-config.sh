#!/bin/bash

# FIST 配置安全合并脚本
# 用于在保留本地配置的情况下合并远程更新

set -e

echo "🔄 FIST 配置安全合并"
echo "===================="

# 1. 备份当前配置
echo "📋 备份当前配置..."
cp docker-compose.yml docker-compose.yml.backup
echo "   ✅ 已备份到 docker-compose.yml.backup"

# 2. 检查是否有本地更改
if git diff --quiet HEAD -- docker-compose.yml; then
    echo "   ℹ️  docker-compose.yml 无本地更改"
    LOCAL_CHANGES=false
else
    echo "   ⚠️  检测到 docker-compose.yml 本地更改"
    LOCAL_CHANGES=true
fi

# 3. 暂存本地更改
if [ "$LOCAL_CHANGES" = true ]; then
    echo "💾 暂存本地更改..."
    git stash push -m "Local docker-compose.yml changes before merge" docker-compose.yml
    echo "   ✅ 本地更改已暂存"
fi

# 4. 拉取远程更新
echo "⬇️  拉取远程更新..."
if git pull origin main; then
    echo "   ✅ 远程更新拉取成功"
else
    echo "   ❌ 远程更新拉取失败"
    if [ "$LOCAL_CHANGES" = true ]; then
        echo "🔄 恢复本地更改..."
        git stash pop
    fi
    exit 1
fi

# 5. 如果有本地更改，尝试合并
if [ "$LOCAL_CHANGES" = true ]; then
    echo "🔀 合并本地配置..."
    
    # 尝试自动合并
    if git stash pop; then
        echo "   ✅ 自动合并成功"
        
        # 检查是否有冲突
        if git diff --check; then
            echo "   ✅ 无合并冲突"
        else
            echo "   ⚠️  检测到合并冲突，需要手动解决"
            echo "   📝 请编辑 docker-compose.yml 解决冲突"
            echo "   🔧 解决后运行: git add docker-compose.yml && git commit"
            exit 1
        fi
    else
        echo "   ❌ 自动合并失败，存在冲突"
        echo "   📝 请手动解决冲突后继续"
        echo "   💡 提示: 您可以参考 docker-compose.yml.backup 中的原始配置"
        exit 1
    fi
fi

# 6. 验证配置
echo "✅ 验证配置..."
if docker-compose config > /dev/null 2>&1; then
    echo "   ✅ docker-compose.yml 配置有效"
else
    echo "   ❌ docker-compose.yml 配置无效"
    echo "   🔄 恢复备份配置..."
    cp docker-compose.yml.backup docker-compose.yml
    echo "   ✅ 已恢复备份配置"
    exit 1
fi

# 7. 显示更改摘要
echo "📊 更改摘要:"
if [ -f docker-compose.yml.backup ]; then
    echo "   📋 配置差异:"
    diff docker-compose.yml.backup docker-compose.yml || true
fi

echo ""
echo "🎉 配置合并完成！"
echo "📝 下一步:"
echo "   1. 检查配置: docker-compose config"
echo "   2. 重新部署: docker-compose up -d"
echo "   3. 验证服务: curl http://localhost:8000/health"
echo ""
echo "💡 备份文件保存在: docker-compose.yml.backup"
