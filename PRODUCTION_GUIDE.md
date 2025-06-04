# FIST 生产环境部署指南

## 🎯 概述

本指南介绍如何在生产环境中部署和管理FIST内容审核系统。

## 🚀 快速开始

### 1. 环境准备

确保您的服务器已安装：
- Docker (>= 20.10)
- Docker Compose (>= 2.0)
- Git

### 2. 克隆项目

```bash
git clone <your-repo-url>
cd fist
```

### 3. 配置API密钥

```bash
# 设置AI服务API密钥
./deploy.sh setup-api
```

### 4. 初始化生产环境

```bash
# 初始化生产环境配置
./deploy.sh init prod
```

### 5. 启动服务

```bash
# 启动所有服务
./deploy.sh start
```

## 🔧 部署脚本使用

### 主要命令

```bash
# 启动服务
./deploy.sh start

# 重启服务 (完全重建)
./deploy.sh restart

# 停止服务
./deploy.sh stop

# 查看服务状态
./deploy.sh status

# 查看服务日志
./deploy.sh logs

# 设置API密钥
./deploy.sh setup-api

# 初始化环境配置
./deploy.sh init [dev|prod|test]

# 备份当前配置
./deploy.sh backup

# 验证配置
./deploy.sh validate

# 查看帮助
./deploy.sh help
```

### 环境配置

- **dev** - 开发环境：启用调试，使用不同端口，禁用部分功能
- **prod** - 生产环境：优化性能，启用所有功能，不暴露数据库端口
- **test** - 测试环境：最小配置，使用内存数据库

## 🔐 安全配置

### 1. 环境变量

生产环境的敏感信息存储在 `.env.local` 文件中：

```bash
# AI 服务配置
AI_API_KEY=your_ai_api_key
AI_API_URL=https://api.openai.com/v1

# 安全配置
SECRET_KEY=your_very_secure_secret_key
ADMIN_PASSWORD=your_secure_admin_password

# 功能开关
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_TOPIC_EXTRACTION=true
ENABLE_TEXT_ANALYSIS=true
ENABLE_MULTILINGUAL=true
ENABLE_CACHING=true
```

### 2. 生产环境配置

生产环境配置文件 `docker-compose.override.yml`：

```yaml
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
```

## 📊 监控和维护

### 1. 健康检查

```bash
# 检查API健康状态
curl http://localhost:8000/

# 查看详细状态
./deploy.sh status
```

### 2. 日志管理

```bash
# 查看实时日志
./deploy.sh logs

# 查看特定服务日志
docker-compose logs fist-api
docker-compose logs db
docker-compose logs redis
```

### 3. 备份和恢复

```bash
# 备份配置
./deploy.sh backup

# 查看备份文件
ls config_backups/
```

## 🔄 更新流程

### 1. 安全更新

```bash
# 1. 备份当前配置
./deploy.sh backup

# 2. 拉取最新代码
git pull origin main

# 3. 验证配置
./deploy.sh validate

# 4. 重新部署
./deploy.sh restart
```

### 2. 回滚操作

如果更新出现问题：

```bash
# 停止服务
./deploy.sh stop

# 回滚到上一个版本
git checkout HEAD~1

# 恢复配置
cp config_backups/docker-compose.override.yml.TIMESTAMP docker-compose.override.yml

# 重新启动
./deploy.sh start
```

## 🆘 故障排除

### 1. 服务启动失败

```bash
# 检查配置
./deploy.sh validate

# 查看详细错误
docker-compose config
./deploy.sh logs

# 完全重置
./deploy.sh stop
docker system prune -f
./deploy.sh start
```

### 2. 端口冲突

```bash
# 检查端口占用
lsof -i :8000
lsof -i :5432
lsof -i :6379

# 修改端口配置
./deploy.sh init dev  # 使用开发环境端口
```

### 3. 数据库连接问题

```bash
# 检查数据库容器状态
docker-compose ps db

# 查看数据库日志
docker-compose logs db

# 重启数据库
docker-compose restart db
```

### 4. 内存不足

```bash
# 检查系统资源
docker stats

# 调整资源限制
# 编辑 docker-compose.override.yml 中的 resources 配置
```

## 📁 文件结构

```
fist/
├── deploy.sh                          # 统一部署管理脚本
├── docker-compose.yml                 # 基础配置（不要修改）
├── docker-compose.override.yml        # 环境配置（Git忽略）
├── .env.local                         # 敏感信息（Git忽略）
├── config_backups/                    # 配置备份目录（Git忽略）
├── PRODUCTION_GUIDE.md               # 生产环境指南
├── README.md                         # 项目说明
├── app.py                           # 主应用文件
├── core/                            # 核心模块
├── routes/                          # API路由
├── ai/                             # AI处理模块
├── utils/                          # 工具模块
└── docs/                           # 文档目录
```

## 🔗 相关链接

- [API 文档](http://localhost:8000/docs)
- [ReDoc 文档](http://localhost:8000/redoc)
- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)

## 📞 获取帮助

如果遇到问题：

1. 查看部署脚本帮助：`./deploy.sh help`
2. 检查日志：`./deploy.sh logs`
3. 验证配置：`./deploy.sh validate`
4. 提交Issue到项目仓库
