# FIST Docker 部署故障排除指南

## 🚨 常见问题及解决方案

### 1. Internal Server Error (500错误)

#### 问题描述
访问 `http://localhost:8000` 返回 Internal Server Error

#### 诊断步骤

**步骤1: 检查容器状态**
```bash
docker-compose ps
```

**步骤2: 查看应用日志**
```bash
docker-compose logs fist-api
```

**步骤3: 检查健康状态**
```bash
curl http://localhost:8000/health
```

#### 常见原因及解决方案

##### 原因1: 环境变量未正确设置
**症状**: 日志显示配置错误或数据库连接失败
**解决方案**:
```bash
# 检查docker-compose.yml中的环境变量
# 确保以下变量已设置:
- DATABASE_URL=postgresql://postgres:fist_password@db:5432/fist_db
- SECRET_KEY=your_secret_key_change_me
- ADMIN_PASSWORD=admin_password_change_me
```

##### 原因2: 数据库连接失败
**症状**: 日志显示数据库连接错误
**解决方案**:
```bash
# 检查数据库容器状态
docker-compose logs db

# 重启数据库容器
docker-compose restart db

# 等待数据库完全启动后重启API
docker-compose restart fist-api
```

##### 原因3: 依赖服务未启动
**症状**: Redis或PostgreSQL连接失败
**解决方案**:
```bash
# 按正确顺序启动服务
docker-compose up -d db redis
sleep 10
docker-compose up -d fist-api
```

### 2. 容器启动失败

#### 问题描述
容器无法启动或立即退出

#### 诊断步骤
```bash
# 查看容器退出状态
docker-compose ps

# 查看详细错误日志
docker-compose logs fist-api

# 检查镜像构建
docker-compose build --no-cache fist-api
```

#### 常见原因及解决方案

##### 原因1: 镜像构建失败
**解决方案**:
```bash
# 清理并重新构建
docker-compose down
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```

##### 原因2: 端口冲突
**症状**: 端口已被占用
**解决方案**:
```bash
# 检查端口占用
lsof -i :8000
lsof -i :5432
lsof -i :6379

# 修改docker-compose.yml中的端口映射
ports:
  - "8001:8000"  # 改为其他端口
```

### 3. 数据库相关问题

#### 问题描述
数据库连接或初始化失败

#### 诊断步骤
```bash
# 检查数据库容器
docker-compose logs db

# 进入数据库容器
docker-compose exec db psql -U postgres -d fist_db

# 检查数据库连接
docker-compose exec fist-api python -c "
from core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection OK')
"
```

#### 解决方案
```bash
# 重置数据库
docker-compose down
docker volume rm fist_postgres_data
docker-compose up -d
```

### 4. Redis缓存问题

#### 问题描述
Redis连接失败（通常不是致命错误）

#### 诊断步骤
```bash
# 检查Redis容器
docker-compose logs redis

# 测试Redis连接
docker-compose exec redis redis-cli ping
```

#### 解决方案
```bash
# Redis失败不会影响核心功能，但可以重启
docker-compose restart redis
```

### 5. 网络连接问题

#### 问题描述
容器间无法通信

#### 诊断步骤
```bash
# 检查网络
docker network ls
docker network inspect fist_fist-network

# 测试容器间连接
docker-compose exec fist-api ping db
docker-compose exec fist-api ping redis
```

#### 解决方案
```bash
# 重建网络
docker-compose down
docker network prune
docker-compose up -d
```

## 🔧 完整重置流程

如果遇到严重问题，可以执行完整重置：

```bash
# 1. 停止所有服务
docker-compose down

# 2. 清理所有相关资源
docker system prune -a -f
docker volume prune -f

# 3. 删除项目相关卷
docker volume rm fist_postgres_data fist_redis_data 2>/dev/null || true

# 4. 重新构建和启动
docker-compose build --no-cache
docker-compose up -d

# 5. 等待服务启动
sleep 30

# 6. 检查状态
docker-compose ps
curl http://localhost:8000/health
```

## 📋 健康检查清单

部署后请检查以下项目：

- [ ] 所有容器都在运行: `docker-compose ps`
- [ ] API健康检查通过: `curl http://localhost:8000/health`
- [ ] 主页可访问: `curl http://localhost:8000/`
- [ ] API文档可访问: `curl http://localhost:8000/docs`
- [ ] 数据库连接正常: 健康检查中database状态为"ok"
- [ ] 日志无严重错误: `docker-compose logs fist-api`

## 🆘 获取帮助

如果问题仍然存在：

1. 收集诊断信息:
```bash
# 保存所有日志
docker-compose logs > fist-logs.txt

# 保存容器状态
docker-compose ps > fist-status.txt

# 保存系统信息
docker version > fist-docker-info.txt
docker-compose version >> fist-docker-info.txt
```

2. 检查GitHub Issues或提交新的Issue
3. 提供完整的错误日志和环境信息
