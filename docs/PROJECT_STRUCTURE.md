# FIST 项目结构

## 📁 目录结构

```
fist/
├── 📄 README.md                    # 项目说明文档
├── 📄 UPGRADE_COMPLETION_REPORT.md # 升级完成报告
├── 📄 PROJECT_STRUCTURE.md         # 项目结构说明
├── 📄 requirements.txt             # Python依赖
├── 📄 pyproject.toml               # 项目配置
├── 📄 .env.example                 # 环境变量示例
│
├── 🚀 app.py                       # 主应用入口
├── ⚙️ config.py                    # 配置管理
├── 🗄️ database.py                  # 数据库连接
├── 📊 models.py                    # 数据模型
│
├── 🔐 auth.py                      # 认证系统
├── 🤖 ai_connector.py              # AI服务连接器
├── 💾 cache.py                     # 基础缓存
├── 📈 monitoring.py                # 监控系统
├── ⚡ background_tasks.py          # 后台任务
├── 📦 batch_processor.py           # 批处理器
│
├── 🌐 api_routes.py                # API路由
├── 👑 admin_routes.py              # 管理员路由
├── 👤 user_routes.py               # 用户路由
├── 🔧 services.py                  # 主要服务
│
├── 📁 services/                    # 增强服务模块
│   ├── 📄 __init__.py              # 服务包初始化
│   ├── 💭 sentiment_analyzer.py   # 情感分析服务
│   ├── 🏷️ topic_extractor.py       # 主题提取服务
│   ├── 📝 text_analyzer.py         # 文本分析服务
│   ├── 🧠 content_processor.py     # 智能内容处理
│   ├── ⚖️ threshold_manager.py     # 动态阈值管理
│   ├── 🤖 ml_models.py             # 机器学习模型
│   ├── 📚 feedback_system.py       # 反馈学习系统
│   ├── 🌍 language_detector.py     # 语言检测
│   ├── 🏛️ cultural_analyzer.py     # 文化分析
│   ├── 🌐 multilingual_processor.py # 多语言处理
│   ├── 💾 semantic_cache.py        # 语义缓存
│   └── 🔧 minimal_analyzer.py      # 最小分析器
│
└── 📁 api/                         # API模块
    └── 📄 index.py                 # API索引
```

## 🔧 核心组件说明

### 🚀 主应用层
- **app.py**: FastAPI应用主入口，路由配置
- **config.py**: 环境配置和设置管理
- **database.py**: PostgreSQL数据库连接和会话管理
- **models.py**: SQLAlchemy数据模型定义

### 🔐 认证和安全
- **auth.py**: JWT令牌认证，用户验证
- **admin_routes.py**: 管理员功能API
- **user_routes.py**: 用户功能API

### 🤖 AI和处理
- **ai_connector.py**: 外部AI服务连接器
- **services.py**: 主要的内容审核服务
- **services/**: 增强AI服务模块目录

### 📊 监控和性能
- **monitoring.py**: 系统监控和指标收集
- **cache.py**: 基础缓存实现
- **background_tasks.py**: 异步后台任务
- **batch_processor.py**: 批量处理功能

### 🌟 增强服务模块

#### Phase 1: 增强文本分析
- **sentiment_analyzer.py**: 多后端情感分析
- **topic_extractor.py**: 智能主题提取
- **text_analyzer.py**: 文本质量分析

#### Phase 2: 智能内容处理
- **content_processor.py**: 语义感知内容处理
- **threshold_manager.py**: 动态阈值管理

#### Phase 3: 高级AI功能
- **ml_models.py**: 机器学习模型集成
- **feedback_system.py**: 实时学习系统

#### Phase 4: 多语言支持
- **language_detector.py**: 高级语言检测
- **cultural_analyzer.py**: 文化上下文分析
- **multilingual_processor.py**: 多语言处理

#### Phase 5: 智能缓存
- **semantic_cache.py**: 语义感知缓存系统

#### 工具模块
- **minimal_analyzer.py**: 轻量级分析器

## 🔄 数据流

```
用户请求 → API路由 → 认证验证 → 内容处理 → AI分析 → 决策输出 → 缓存存储 → 响应返回
    ↓
语言检测 → 文化分析 → 增强分析 → 智能处理 → ML预测 → 动态阈值 → 反馈学习
```

## 🚀 部署文件

- **requirements.txt**: 生产环境依赖
- **pyproject.toml**: 项目配置和开发依赖
- **.env.example**: 环境变量配置示例

## 📚 文档文件

- **README.md**: 项目介绍和使用指南
- **UPGRADE_COMPLETION_REPORT.md**: 详细升级报告
- **PROJECT_STRUCTURE.md**: 本文件，项目结构说明

## 🎯 模块化设计

每个服务模块都是独立的，支持：
- ✅ 独立测试
- ✅ 按需加载
- ✅ 优雅降级
- ✅ 配置控制
- ✅ 性能监控

这种结构确保了系统的可维护性、可扩展性和生产稳定性。
