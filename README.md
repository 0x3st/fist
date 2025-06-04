# FIST - Fast Intelligent Security Text

🚀 **FIST v2.0** - 企业级AI驱动的内容审核API平台

FIST是一个现代化的智能内容审核系统，提供纯API服务，集成了先进的人工智能、多语言处理、智能缓存和实时监控技术，为内容平台提供精准、高效、可扩展的内容审核服务。

## ✨ 核心特性

### 🤖 **AI驱动的智能分析**
- **多维度分析**: 情感分析、主题提取、文本质量评估
- **智能内容处理**: 基于语义重要性的内容选择和处理
- **自适应决策**: 动态阈值管理和上下文感知决策

### 🌍 **多语言和文化感知**
- **多语言支持**: 智能语言检测和处理
- **文化上下文分析**: 多文化区域的敏感性检测
- **跨语言内容理解**: 智能处理混合语言内容

### ⚡ **高性能架构**
- **语义智能缓存**: 高效缓存机制，显著提升响应速度
- **批处理支持**: 大规模内容并行处理
- **实时监控**: 完整的性能监控和分析

### 🔧 **企业级特性**
- **纯API服务**: RESTful API设计，易于集成
- **Token认证**: 安全的用户和管理员认证系统
- **灵活配置**: 模块化设计，按需启用功能
- **数据安全**: 哈希存储，隐私保护

## 🚀 Docker 快速部署

### 📋 系统要求

**Docker 环境:**
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM, 2+ CPU核心

**生产环境:**
- Docker 24.0+
- Docker Compose 2.20+
- 8GB+ RAM, 4+ CPU核心

### 🐳 Docker 部署

#### 1. 克隆项目
```bash
git clone <repository-url>
cd fist
```

#### 2. 启动服务

**方式一：使用快速启动脚本（推荐）**
```bash
# 运行快速启动脚本
./docker-start.sh
```

**方式二：手动启动**
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f fist-api
```

#### 3. 验证部署
```bash
# 检查API状态
curl http://localhost:8000/

# 查看API文档
# 访问 http://localhost:8000/docs
```

#### 4. 配置环境变量
编辑 `docker-compose.yml` 中的环境变量：
```yaml
environment:
  - DATABASE_URL=postgresql://postgres:fist_password@db:5432/fist_db
  - REDIS_URL=redis://redis:6379
  - ADMIN_PASSWORD=your_secure_admin_password  # 修改此密码
  - SECRET_KEY=your_secret_key_change_me       # 修改此密钥
  - AI_API_KEY=your_ai_api_key                # 配置AI服务密钥
  - ENABLE_SENTIMENT_ANALYSIS=true
  - ENABLE_TOPIC_EXTRACTION=true
  - ENABLE_TEXT_ANALYSIS=true
  - ENABLE_MULTILINGUAL=true
  - ENABLE_CACHING=true
  - DEBUG=false
```

## 📊 Docker 部署配置

### 🎯 **开发环境** (本地测试)
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  fist-api:
    environment:
      - DEBUG=true
      - ENABLE_MULTILINGUAL=false
      - ENABLE_CACHING=false
    ports:
      - "8000:8000"
```

### 🚀 **生产环境** (推荐配置)
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  fist-api:
    environment:
      - DEBUG=false
      - ENABLE_SENTIMENT_ANALYSIS=true
      - ENABLE_TOPIC_EXTRACTION=true
      - ENABLE_TEXT_ANALYSIS=true
      - ENABLE_MULTILINGUAL=true
      - ENABLE_CACHING=true
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  # 移除端口暴露以提高安全性
  db:
    ports: []
  redis:
    ports: []
```

### 🌟 **高性能部署** (大规模应用)
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  fist-api:
    environment:
      - MAX_BATCH_SIZE=2000
      - CACHE_TTL=7200
      - WORKER_THREADS=8
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G
```

## 🔌 API 接口

### 🔐 **认证接口**
```bash
# 管理员登录
POST /api/admin/login
{
  "password": "admin_password"
}

# 用户注册 (管理员操作)
POST /api/admin/users
Authorization: Bearer ADMIN_TOKEN
{
  "username": "user@example.com",
  "password": "user_password"
}

# 用户登录
POST /api/users/login
{
  "username": "user@example.com",
  "password": "user_password"
}
```

### 🤖 **内容审核接口**
```bash
# 单个内容审核
POST /api/moderate
Authorization: Bearer YOUR_TOKEN
{
  "content": "要审核的文本内容",
  "percentages": [0.8],
  "thresholds": [20, 80],
  "enable_enhanced_analysis": true
}

# 批量内容审核
POST /api/batch/create
Authorization: Bearer YOUR_TOKEN
{
  "contents": ["内容1", "内容2", "内容3"],
  "percentages": [0.8],
  "thresholds": [20, 80]
}

# 响应示例
{
  "final_decision": "A",  // A=通过, M=人工审核, R=拒绝
  "reason": "内容安全，情感积极",
  "ai_result": {
    "inappropriate_probability": 15,
    "reason": "内容健康正面"
  },
  "pierced_content": "要审核的文本内容",
  "percentage_used": 80.0,
  "processing_time": 0.123,
  "enhanced_analysis": {
    "sentiment_analysis": {...},
    "topic_extraction": {...}
  }
}
```

### 📊 **管理接口**
```bash
# 用户管理
GET /api/admin/users
POST /api/admin/users
PUT /api/admin/users/{user_id}
DELETE /api/admin/users/{user_id}

# Token管理
GET /api/users/tokens
POST /api/users/tokens
DELETE /api/users/tokens/{token_id}

# 批处理管理
GET /api/batch/{job_id}/status
GET /api/batch/{job_id}/results

# 系统配置
GET /api/admin/config
PUT /api/admin/config
```

## 💻 Docker 使用示例

### 基本使用
```bash
# 启动服务
docker-compose up -d

# 测试API
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password": "admin_password_change_me"}'

# 获取token后进行内容审核
curl -X POST http://localhost:8000/api/moderate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "content": "这是一条测试消息",
    "percentages": [0.8],
    "thresholds": [20, 80],
    "enable_enhanced_analysis": true
  }'
```

### 生产环境部署
```bash
# 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 扩展服务实例
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d --scale fist-api=3

# 查看服务状态
docker-compose ps
docker-compose logs -f fist-api
```

### 维护操作
```bash
# 备份数据库
docker exec fist-postgres pg_dump -U postgres fist_db > backup_$(date +%Y%m%d).sql

# 更新服务
git pull origin main
docker-compose build
docker-compose up -d

# 查看资源使用
docker stats
```

## 🔧 Docker 高级配置

### 🎛️ **环境变量配置**
在 `docker-compose.yml` 中配置：
```yaml
environment:
  # 核心配置
  - SECRET_KEY=your_secret_key_here
  - ADMIN_PASSWORD=your_admin_password
  - DEBUG=false

  # 数据库配置
  - DATABASE_URL=postgresql://postgres:fist_password@db:5432/fist_db
  - REDIS_URL=redis://redis:6379

  # AI服务配置
  - AI_API_KEY=your_ai_api_key
  - AI_API_URL=https://api.your-ai-service.com

  # 功能开关
  - ENABLE_SENTIMENT_ANALYSIS=true
  - ENABLE_TOPIC_EXTRACTION=true
  - ENABLE_TEXT_ANALYSIS=true
  - ENABLE_MULTILINGUAL=true
  - ENABLE_CACHING=true

  # 性能配置
  - MAX_CONTENT_LENGTH=10000
  - MAX_BATCH_SIZE=1000
  - CACHE_TTL=3600
  - WORKER_THREADS=4
```

### 🐳 **Docker 服务配置**
```yaml
# 完整的 docker-compose.yml 配置
version: '3.8'

services:
  # FIST API Service
  fist-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:fist_password@db:5432/fist_db
      - REDIS_URL=redis://redis:6379
      - ADMIN_PASSWORD=admin_password_change_me
      - SECRET_KEY=your_secret_key_change_me
    depends_on:
      - db
      - redis
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - fist-network

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: fist_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: fist_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - fist-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - fist-network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - fist-api
    restart: unless-stopped
    networks:
      - fist-network

volumes:
  postgres_data:
  redis_data:

networks:
  fist-network:
    driver: bridge
```

## 📈 Docker 性能监控

### 📊 **容器监控**
```bash
# 查看容器资源使用
docker stats

# 查看容器日志
docker-compose logs -f fist-api

# 查看服务状态
docker-compose ps
```

### 🔍 **监控集成**
添加监控服务到 `docker-compose.yml`：
```yaml
services:
  # Prometheus 监控
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - fist-network

  # Grafana 可视化
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    networks:
      - fist-network
```

## 🛠️ 开发指南

### 📁 **Docker 项目结构**
```
fist/
├── Dockerfile               # Docker镜像构建文件
├── docker-compose.yml       # Docker Compose配置
├── docker-start.sh          # Docker快速启动脚本
├── .dockerignore           # Docker忽略文件
├── nginx.conf              # Nginx反向代理配置
├── app.py                  # FastAPI主应用
├── pyproject.toml          # 项目配置和依赖
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── models.py           # 数据模型
│   ├── database.py         # 数据库操作
│   ├── auth.py             # 认证系统
│   └── moderation.py       # 内容审核核心
├── routes/                 # API路由
│   ├── api_routes.py       # 内容审核API
│   ├── user_routes.py      # 用户管理API
│   └── admin_routes.py     # 管理员API
├── utils/                  # 工具模块
│   ├── cache.py            # 缓存管理
│   ├── monitoring.py       # 性能监控
│   ├── batch_processor.py  # 批处理
│   └── background_tasks.py # 后台任务
├── ai/                     # AI分析模块
│   ├── ai_connector.py     # AI服务连接
│   ├── sentiment_analyzer.py
│   ├── topic_extractor.py
│   ├── text_analyzer.py
│   └── ...                 # 其他AI模块
└── docs/                   # 文档
    └── DEPLOYMENT.md       # Docker部署文档
```

### 🔧 **Docker 开发和测试**
```bash
# 构建镜像
docker-compose build

# 启动开发环境
docker-compose up -d

# 查看日志
docker-compose logs -f fist-api

# 运行测试
docker-compose exec fist-api python -m pytest tests/

# 进入容器调试
docker-compose exec fist-api bash
```

## 🔒 安全特性

### 🛡️ **数据安全**
- 所有敏感数据使用 SHA-256 哈希存储
- JWT Token 认证系统
- 用户权限管理和访问控制
- 隐私保护，不存储原始内容

### 🔐 **API安全**
- Token 基础的认证
- 管理员和用户权限分离
- 安全的密码存储和验证
- CORS 配置和请求验证

## 📚 Docker 文档和支持

### 📖 **详细文档**
- [API 文档](http://localhost:8000/docs) - 交互式API文档 (启动后访问)
- [ReDoc 文档](http://localhost:8000/redoc) - 详细的API文档
- [Docker 部署文档](docs/DEPLOYMENT.md) - 完整的Docker部署指南

### 🆘 **技术支持**
- Docker 容器日志和监控
- 容器性能指标和分析
- Docker 故障排除和优化建议

## 🎯 版本信息

**当前版本**: FIST v2.0 - 企业级AI驱动的内容审核API平台

### 🚀 **v2.0 核心特性**
- ✅ 纯API服务架构，易于集成
- ✅ AI驱动的多维度内容分析
- ✅ 智能内容处理和缓存
- ✅ 批处理和实时监控
- ✅ 企业级安全和权限管理

### 📈 **技术优势**
- 模块化设计，灵活配置
- 高性能并发处理
- 智能缓存机制
- 完整的监控和日志
- 多种部署方式支持

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**FIST v2.0 - 现代化的企业级内容审核API平台** 🚀
