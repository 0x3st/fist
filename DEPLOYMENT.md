# FIST Docker 部署指南

本文档提供了 FIST 内容审核API平台的Docker部署指南。

## 🚀 快速部署

### Docker Compose 部署

1. **克隆项目**
```bash
git clone <repository-url>
cd fist
```

2. **配置环境变量**
```bash
# 编辑 docker-compose.yml 中的环境变量，或创建 .env 文件
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

## 🔧 Docker 配置

### 环境变量配置

在 `docker-compose.yml` 中配置以下环境变量：

```yaml
environment:
  - DATABASE_URL=postgresql://postgres:fist_password@db:5432/fist_db
  - REDIS_URL=redis://redis:6379
  - ADMIN_PASSWORD=admin_password_change_me
  - SECRET_KEY=your_secret_key_change_me
  - ENABLE_SENTIMENT_ANALYSIS=true
  - ENABLE_TOPIC_EXTRACTION=true
  - ENABLE_TEXT_ANALYSIS=true
  - ENABLE_MULTILINGUAL=true
  - ENABLE_CACHING=true
  - DEBUG=false
```

### 服务组件

Docker Compose 包含以下服务：

- **fist-api**: 主应用服务
- **db**: PostgreSQL 数据库
- **redis**: Redis 缓存
- **nginx**: 反向代理（可选）

## 🌐 生产环境部署

### 生产环境配置

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

### Kubernetes 部署

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

## 🔒 Docker 安全配置

### SSL/TLS 配置

在 `nginx.conf` 中配置 SSL：

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

### 密码和密钥管理

```bash
# 生成强密码
openssl rand -base64 32

# 生成 JWT 密钥
openssl rand -hex 32
```

## 📊 Docker 监控和日志

### 日志配置

在 `docker-compose.yml` 中配置日志：

```yaml
services:
  fist-api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 健康检查

Docker 容器内置健康检查：

```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1
```

### 监控集成

使用 Docker Compose 添加监控服务：

```yaml
# 添加到 docker-compose.yml
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

## 🔧 Docker 维护和更新

### 备份策略

```bash
# 数据库备份
docker exec fist-postgres pg_dump -U postgres fist_db > backup_$(date +%Y%m%d).sql

# Redis 备份
docker exec fist-redis redis-cli BGSAVE

# 数据卷备份
docker run --rm -v fist_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### 更新部署

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

### 性能优化

在 `docker-compose.yml` 中调整资源限制：

```yaml
services:
  fist-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## 🚨 Docker 故障排除

### 常见问题

1. **容器启动失败**
```bash
# 检查容器状态
docker-compose ps
# 查看容器日志
docker-compose logs fist-api
docker-compose logs db
docker-compose logs redis
```

2. **数据库连接失败**
```bash
# 检查数据库容器
docker-compose logs db
# 进入数据库容器
docker-compose exec db psql -U postgres -d fist_db
```

3. **API 响应慢**
```bash
# 检查容器资源使用
docker stats
# 查看应用日志
docker-compose logs fist-api
```

### 性能调优

在 `docker-compose.yml` 中优化配置：

```yaml
services:
  fist-api:
    environment:
      - WORKER_THREADS=8
      - MAX_BATCH_SIZE=2000
      - CACHE_TTL=7200
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

## 📞 支持

如果遇到Docker部署问题，请：

1. 检查 `docker-compose logs`
2. 验证 `docker-compose.yml` 配置
3. 确认容器网络连接
4. 查看容器资源使用情况

更多技术支持，请参考项目文档或提交 Issue。
