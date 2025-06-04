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

## 🚀 快速部署

### 📋 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM, 2+ CPU核心
- 稳定的互联网连接（用于AI API调用）

### 🐳 Docker 部署

#### 1. 克隆项目
```bash
git clone <repository-url>
cd fist
```

#### 2. 设置API密钥
```bash
./deploy.sh setup-api
```

#### 3. 初始化环境
```bash
# 生产环境
./deploy.sh init prod

# 或开发环境
./deploy.sh init dev
```

#### 4. 启动服务
```bash
./deploy.sh start
```

#### 5. 验证部署
```bash
# 检查API状态
curl http://localhost:8000/

# 查看API文档
# 访问 http://localhost:8000/docs
```

### 🔧 常用命令

```bash
./deploy.sh help       # 查看所有命令
./deploy.sh start      # 启动服务
./deploy.sh stop       # 停止服务
./deploy.sh restart    # 重启服务
./deploy.sh status     # 查看状态
./deploy.sh logs       # 查看日志
./deploy.sh backup     # 备份配置
./deploy.sh validate   # 验证配置
```

## 📖 详细文档

- **快速部署**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **生产环境**: [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)
- **项目结构**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- **依赖管理**: [docs/DEPENDENCY_MANAGEMENT.md](docs/DEPENDENCY_MANAGEMENT.md)

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

### 基本使用
```bash
# 启动服务
./deploy.sh start

# 测试API
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your_admin_password"}'

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

## 🚨 故障排除

如果遇到问题：

1. 查看部署脚本帮助：`./deploy.sh help`
2. 检查服务日志：`./deploy.sh logs`
3. 验证配置：`./deploy.sh validate`
4. 参考详细指南：[生产环境部署指南](PRODUCTION_GUIDE.md)

### 常见问题

- **端口冲突**: 使用 `./deploy.sh init dev` 切换到开发环境端口
- **服务启动失败**: 运行 `./deploy.sh validate` 检查配置
- **API连接问题**: 确认服务状态 `./deploy.sh status`

## 📚 文档和支持

### 📖 **在线文档**
- [API 文档](http://localhost:8000/docs) - 交互式API文档 (启动后访问)
- [ReDoc 文档](http://localhost:8000/redoc) - 详细的API文档

## 🎯 版本信息

**当前版本**: FIST v2.0 - 企业级AI驱动的内容审核API平台

### 🚀 **核心特性**
- ✅ 纯API服务架构，易于集成
- ✅ AI驱动的多维度内容分析
- ✅ 智能内容处理和缓存
- ✅ 批处理和实时监控
- ✅ 企业级安全和权限管理

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**FIST v2.0 - 现代化的企业级内容审核API平台** 🚀
