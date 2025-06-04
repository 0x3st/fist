# FIST 配置管理指南

## 🎯 概述

本指南介绍如何在保留个人配置的情况下安全地更新FIST应用，避免配置冲突。

## 🔧 配置管理方案

### 方案1: 使用 Override 配置文件

Docker Compose 支持自动合并 `docker-compose.override.yml` 文件，这是推荐的方法。

#### 快速开始

```bash
# 1. 初始化开发环境配置
./config-manager.sh init dev

# 2. 启动服务
docker-compose up -d

# 3. 验证配置
./config-manager.sh validate
```

#### 环境类型

- **dev** - 开发环境：启用调试，使用不同端口，禁用部分功能
- **prod** - 生产环境：优化性能，启用所有功能，不暴露数据库端口
- **test** - 测试环境：最小配置，使用内存数据库

### 方案2: 配置备份与合并

如果您已经有自定义配置，使用安全合并脚本：

```bash
# 安全合并远程更新
./merge-config.sh
```

## 📋 常用操作

### 初始化环境配置

```bash
# 开发环境
./config-manager.sh init dev

# 生产环境  
./config-manager.sh init prod

# 测试环境
./config-manager.sh init test
```

### 备份当前配置

```bash
# 备份配置
./config-manager.sh backup

# 查看备份
ls config_backups/
```

### 验证配置

```bash
# 验证配置有效性
./config-manager.sh validate

# 查看当前状态
./config-manager.sh status
```

### 切换环境

```bash
# 切换到生产环境
./config-manager.sh switch prod

# 重新部署
docker-compose down
docker-compose up -d
```

## 🔄 更新流程

### 安全更新步骤

1. **备份当前配置**
```bash
./config-manager.sh backup
```

2. **拉取远程更新**
```bash
git pull origin main
```

3. **如果有冲突，使用合并脚本**
```bash
./merge-config.sh
```

4. **验证配置**
```bash
./config-manager.sh validate
```

5. **重新部署**
```bash
docker-compose down
docker-compose up -d
```

### 自动化更新脚本

```bash
#!/bin/bash
# update-fist.sh

echo "🔄 更新FIST应用..."

# 备份配置
./config-manager.sh backup

# 拉取更新
if git pull origin main; then
    echo "✅ 代码更新成功"
else
    echo "❌ 代码更新失败，请手动解决冲突"
    exit 1
fi

# 验证配置
if ./config-manager.sh validate; then
    echo "✅ 配置验证通过"
else
    echo "❌ 配置验证失败"
    exit 1
fi

# 重新部署
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 健康检查
sleep 30
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "🎉 更新完成，服务正常运行"
else
    echo "⚠️ 服务可能存在问题，请检查日志"
    docker-compose logs fist-api
fi
```

## 📁 文件结构

```
fist/
├── docker-compose.yml              # 基础配置（不要修改）
├── docker-compose.override.yml     # 个人配置（Git忽略）
├── docker-compose.override.yml.example  # 配置示例
├── config-manager.sh              # 配置管理脚本
├── merge-config.sh                # 安全合并脚本
├── config_backups/                # 配置备份目录（Git忽略）
│   ├── docker-compose.override.yml.20240101_120000
│   └── .env.20240101_120000
└── .gitignore                     # 忽略个人配置文件
```

## 🔐 安全最佳实践

### 1. 敏感信息管理

```bash
# 创建 .env.local 文件存储敏感信息
cat > .env.local << EOF
SECRET_KEY=your_very_secure_secret_key
ADMIN_PASSWORD=your_secure_admin_password
AI_API_KEY=your_ai_api_key
DATABASE_PASSWORD=your_database_password
EOF

# 在 docker-compose.override.yml 中引用
env_file:
  - .env.local
```

### 2. 生产环境配置

```yaml
# docker-compose.override.yml (生产环境)
version: '3.8'
services:
  fist-api:
    environment:
      - DEBUG=false
      - SECRET_KEY=${SECRET_KEY}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
  
  db:
    ports: []  # 不暴露数据库端口
    environment:
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
  
  redis:
    ports: []  # 不暴露Redis端口
```

### 3. 开发环境配置

```yaml
# docker-compose.override.yml (开发环境)
version: '3.8'
services:
  fist-api:
    environment:
      - DEBUG=true
      - ENABLE_CACHING=false
    ports:
      - "8001:8000"  # 避免端口冲突
    volumes:
      - ./logs:/app/logs
      - ./dev-data:/app/data
  
  db:
    ports:
      - "5433:5432"  # 开发环境可以暴露端口
```

## 🆘 故障排除

### 配置冲突

如果遇到配置冲突：

```bash
# 1. 查看冲突文件
git status

# 2. 备份本地更改
cp docker-compose.yml docker-compose.yml.backup

# 3. 重置到远程版本
git checkout HEAD -- docker-compose.yml

# 4. 重新应用本地配置
./config-manager.sh init dev  # 或其他环境
```

### 服务启动失败

```bash
# 1. 验证配置
./config-manager.sh validate

# 2. 查看详细错误
docker-compose config
docker-compose logs

# 3. 完全重置
docker-compose down
docker system prune -f
docker-compose up -d
```

## 📞 获取帮助

- 查看配置管理器帮助：`./config-manager.sh help`
- 查看故障排除指南：[DOCKER_TROUBLESHOOTING.md](DOCKER_TROUBLESHOOTING.md)
- 提交Issue：[GitHub Issues](https://github.com/your-repo/fist/issues)
