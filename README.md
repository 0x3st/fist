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

## 🚀 快速开始

### 📋 系统要求

**最低配置:**
- Python 3.8+
- PostgreSQL 12+ (或 SQLite 用于开发)
- 2GB RAM, 2 CPU核心

**推荐配置:**
- Python 3.10+
- PostgreSQL 14+
- Redis (可选，用于缓存)
- 4GB RAM, 4 CPU核心

**生产环境:**
- Python 3.11+
- PostgreSQL 15+
- Redis 6+
- 8GB+ RAM, 8+ CPU核心

### 🛠️ 安装部署

#### 1. 克隆项目
```bash
git clone <repository-url>
cd fist
```

#### 2. 环境设置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖 (推荐使用 uv)
pip install uv
uv pip install -e .

# 或使用传统方式
pip install -e .
```

#### 3. 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/fist_db
# 或使用 SQLite (开发环境)
# DATABASE_URL=sqlite:///./fist.db

# AI服务配置
AI_API_KEY=your_ai_api_key
AI_API_URL=https://api.your-ai-service.com

# 系统配置
ADMIN_PASSWORD=your_secure_admin_password
SECRET_KEY=your_secret_key

# Redis配置 (可选)
REDIS_URL=redis://localhost:6379

# 功能开关 (可选)
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_TOPIC_EXTRACTION=true
ENABLE_TEXT_ANALYSIS=true
ENABLE_MULTILINGUAL=false
ENABLE_CACHING=true
```

#### 4. 启动应用
```bash
# 开发模式
python app.py

# 或使用 uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

应用将在 `http://localhost:8000` 启动

#### 5. 验证安装
```bash
# 检查API状态
curl http://localhost:8000/

# 查看API文档
# 访问 http://localhost:8000/docs
```

## 📊 部署配置

### 🎯 **开发环境** (本地开发)
```env
DATABASE_URL=sqlite:///./fist.db
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_TOPIC_EXTRACTION=true
ENABLE_TEXT_ANALYSIS=true
ENABLE_MULTILINGUAL=false
ENABLE_CACHING=false
DEBUG=true
```

### 🚀 **生产环境** (推荐配置)
```env
DATABASE_URL=postgresql://user:password@localhost/fist_db
REDIS_URL=redis://localhost:6379
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_TOPIC_EXTRACTION=true
ENABLE_TEXT_ANALYSIS=true
ENABLE_MULTILINGUAL=true
ENABLE_CACHING=true
DEBUG=false
```

### 🌟 **高性能部署** (大规模应用)
```env
# 数据库配置
DATABASE_URL=postgresql://user:password@db-cluster/fist_db
REDIS_URL=redis://redis-cluster:6379

# 功能配置
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_TOPIC_EXTRACTION=true
ENABLE_TEXT_ANALYSIS=true
ENABLE_MULTILINGUAL=true
ENABLE_CACHING=true

# 性能配置
MAX_BATCH_SIZE=1000
CACHE_TTL=3600
WORKER_THREADS=8
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

## 💻 使用示例

### Python 客户端
```python
import requests

class FISTClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}

    def moderate_content(self, content, percentages=None, thresholds=None, enhanced_analysis=True):
        data = {
            'content': content,
            'enable_enhanced_analysis': enhanced_analysis
        }
        if percentages:
            data['percentages'] = percentages
        if thresholds:
            data['thresholds'] = thresholds

        response = requests.post(
            f'{self.base_url}/api/moderate',
            json=data,
            headers=self.headers
        )
        return response.json()

    def batch_moderate(self, contents, percentages=None, thresholds=None):
        data = {'contents': contents}
        if percentages:
            data['percentages'] = percentages
        if thresholds:
            data['thresholds'] = thresholds

        response = requests.post(
            f'{self.base_url}/api/batch/create',
            json=data,
            headers=self.headers
        )
        return response.json()

# 使用示例
client = FISTClient('http://localhost:8000', 'your_token')

# 基础审核
result = client.moderate_content('这是一条测试消息')
print(f"决策: {result['final_decision']}, 原因: {result['reason']}")

# 自定义阈值审核
result = client.moderate_content(
    '这是一条测试消息',
    percentages=[0.8],
    thresholds=[20, 80],
    enhanced_analysis=True
)

# 批量审核
batch_result = client.batch_moderate([
    '消息1', '消息2', '消息3'
], percentages=[0.8], thresholds=[20, 80])
print(f"批处理任务ID: {batch_result['job_id']}")
```

### JavaScript 客户端
```javascript
class FISTClient {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async moderateContent(content, options = {}) {
        const data = {
            content,
            enable_enhanced_analysis: options.enhanced_analysis || true
        };

        if (options.percentages) data.percentages = options.percentages;
        if (options.thresholds) data.thresholds = options.thresholds;

        const response = await fetch(`${this.baseUrl}/api/moderate`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        return response.json();
    }

    async batchModerate(contents, options = {}) {
        const data = { contents };
        if (options.percentages) data.percentages = options.percentages;
        if (options.thresholds) data.thresholds = options.thresholds;

        const response = await fetch(`${this.baseUrl}/api/batch/create`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        return response.json();
    }
}

// 使用示例
const client = new FISTClient('http://localhost:8000', 'your_token');

// 基础审核
client.moderateContent('This is a test message')
    .then(result => {
        console.log(`Decision: ${result.final_decision}, Reason: ${result.reason}`);
    });

// 批量审核
client.batchModerate(['Message 1', 'Message 2', 'Message 3'], {
    percentages: [0.8],
    thresholds: [20, 80]
}).then(result => {
    console.log(`Batch job ID: ${result.job_id}`);
});
```

## 🔧 高级配置

### 🎛️ **环境变量配置**
```env
# 核心配置
SECRET_KEY=your_secret_key_here
ADMIN_PASSWORD=your_admin_password
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/fist_db
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

### 🌍 **Docker 部署**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv pip install -e .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  fist-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/fist_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: fist_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

## 📈 性能监控

### 📊 **系统指标**
- **处理速度**: 平均响应时间 < 200ms
- **缓存效率**: 智能语义缓存
- **批处理**: 支持大规模并行处理
- **可用性**: 优雅降级，确保服务可用性

### 🔍 **监控功能**
- 实时性能监控
- API调用统计
- 缓存命中率分析
- 错误率监控
- 批处理任务状态跟踪

## 🛠️ 开发指南

### 📁 **项目结构**
```
fist/
├── app.py                    # FastAPI主应用
├── pyproject.toml           # 项目配置和依赖
├── .env.example             # 环境变量示例
├── api/
│   └── index.py             # Vercel部署入口
├── core/                    # 核心模块
│   ├── __init__.py
│   ├── config.py            # 配置管理
│   ├── models.py            # 数据模型
│   ├── database.py          # 数据库操作
│   ├── auth.py              # 认证系统
│   └── moderation.py        # 内容审核核心
├── routes/                  # API路由
│   ├── api_routes.py        # 内容审核API
│   ├── user_routes.py       # 用户管理API
│   └── admin_routes.py      # 管理员API
├── utils/                   # 工具模块
│   ├── cache.py             # 缓存管理
│   ├── monitoring.py        # 性能监控
│   ├── batch_processor.py   # 批处理
│   └── background_tasks.py  # 后台任务
├── ai/                      # AI分析模块
│   ├── ai_connector.py      # AI服务连接
│   ├── sentiment_analyzer.py
│   ├── topic_extractor.py
│   ├── text_analyzer.py
│   └── ...                  # 其他AI模块
├── client_libraries/        # 客户端库
│   ├── python/
│   ├── javascript/
│   └── ...
└── docs/                    # 文档
    ├── API.md
    ├── DEPLOYMENT.md
    └── ...
```

### 🔧 **开发和测试**
```bash
# 运行测试
python -m pytest tests/

# 代码格式化
black .
isort .

# 类型检查
mypy .

# 启动开发服务器
uvicorn app:app --reload --host 0.0.0.0 --port 8000
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

## 📚 文档和支持

### 📖 **详细文档**
- [API 文档](http://localhost:8000/docs) - 交互式API文档 (启动后访问)
- [ReDoc 文档](http://localhost:8000/redoc) - 详细的API文档
- [项目结构](FINAL_STRUCTURE.md) - 完整的项目结构说明
- [客户端库](client_libraries/) - 多语言客户端库

### 🆘 **技术支持**
- 完整的错误日志和监控
- 性能指标和分析
- 故障排除和优化建议

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
