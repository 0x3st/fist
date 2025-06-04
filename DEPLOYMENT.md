# FIST 部署指南

本文档提供了 FIST 内容审核API平台的详细部署指南。

## 🚀 快速部署

### Docker Compose 部署 (推荐)

1. **克隆项目**
```bash
git clone <repository-url>
cd fist
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的配置
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **验证部署**
```bash
curl http://localhost:8000/
curl http://localhost:8000/docs
```

## 🔧 详细配置

### 环境变量配置

创建 `.env` 文件并配置以下变量：

```env
# 核心配置
SECRET_KEY=your_very_secure_secret_key_here
ADMIN_PASSWORD=your_secure_admin_password
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/fist_db

# Redis配置 (可选，用于缓存)
REDIS_URL=redis://localhost:6379

# AI服务配置
AI_API_KEY=your_ai_api_key
AI_API_URL=https://api.your-ai-service.com

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

# API配置
API_HOST=0.0.0.0
API_PORT=8000
```

### 数据库配置

#### PostgreSQL (推荐)
```bash
# 创建数据库
createdb fist_db

# 或使用 Docker
docker run -d \
  --name fist-postgres \
  -e POSTGRES_DB=fist_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15
```

#### SQLite (开发环境)
```env
DATABASE_URL=sqlite:///./fist.db
```

### Redis 配置 (可选)

```bash
# 使用 Docker 运行 Redis
docker run -d \
  --name fist-redis \
  -p 6379:6379 \
  redis:7-alpine
```

## 🌐 生产环境部署

### 1. 使用 Docker Compose

```bash
# 生产环境配置
cp docker-compose.yml docker-compose.prod.yml

# 编辑生产配置
# - 移除端口暴露 (5432, 6379)
# - 配置 SSL 证书
# - 设置强密码
# - 配置日志轮转

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Kubernetes 部署

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fist-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fist-api
  template:
    metadata:
      labels:
        app: fist-api
    spec:
      containers:
      - name: fist-api
        image: fist:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: fist-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: fist-secrets
              key: secret-key
---
apiVersion: v1
kind: Service
metadata:
  name: fist-api-service
spec:
  selector:
    app: fist-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. 云平台部署

#### Vercel 部署
```bash
# 使用 Vercel CLI
npm i -g vercel
vercel

# 或使用 GitHub 集成
# 1. 连接 GitHub 仓库到 Vercel
# 2. 配置环境变量
# 3. 自动部署
```

#### AWS ECS 部署
```bash
# 构建并推送镜像到 ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-west-2.amazonaws.com
docker build -t fist .
docker tag fist:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/fist:latest
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/fist:latest

# 创建 ECS 任务定义和服务
```

## 🔒 安全配置

### 1. SSL/TLS 配置

```nginx
# nginx SSL 配置
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # 强化 SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

### 2. 防火墙配置

```bash
# UFW 配置
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### 3. 密码和密钥管理

```bash
# 生成强密码
openssl rand -base64 32

# 生成 JWT 密钥
openssl rand -hex 32
```

## 📊 监控和日志

### 1. 日志配置

```yaml
# docker-compose.yml 日志配置
services:
  fist-api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 2. 健康检查

```bash
# 健康检查脚本
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ $response -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy"
    exit 1
fi
```

### 3. 监控集成

```yaml
# Prometheus 监控
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 🔧 维护和更新

### 1. 备份策略

```bash
# 数据库备份
docker exec fist-postgres pg_dump -U postgres fist_db > backup_$(date +%Y%m%d).sql

# Redis 备份
docker exec fist-redis redis-cli BGSAVE
```

### 2. 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建和部署
docker-compose build
docker-compose up -d

# 检查服务状态
docker-compose ps
docker-compose logs fist-api
```

### 3. 性能优化

```bash
# 调整 worker 数量
uvicorn app:app --workers 8 --host 0.0.0.0 --port 8000

# 配置数据库连接池
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=30
```

## 🚨 故障排除

### 常见问题

1. **数据库连接失败**
```bash
# 检查数据库状态
docker-compose logs db
# 验证连接字符串
psql $DATABASE_URL
```

2. **Redis 连接失败**
```bash
# 检查 Redis 状态
docker-compose logs redis
# 测试连接
redis-cli -u $REDIS_URL ping
```

3. **API 响应慢**
```bash
# 检查资源使用
docker stats
# 查看日志
docker-compose logs fist-api
```

### 性能调优

1. **数据库优化**
```sql
-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_tokens_user_id ON tokens(user_id);
```

2. **缓存优化**
```env
# 增加缓存时间
CACHE_TTL=7200
# 启用缓存压缩
ENABLE_CACHE_COMPRESSION=true
```

3. **应用优化**
```env
# 增加工作线程
WORKER_THREADS=8
# 调整批处理大小
MAX_BATCH_SIZE=2000
```

## 📞 支持

如果遇到部署问题，请：

1. 检查日志文件
2. 验证环境变量配置
3. 确认网络连接
4. 查看系统资源使用情况

更多技术支持，请参考项目文档或提交 Issue。
