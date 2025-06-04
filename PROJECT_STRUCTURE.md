# FIST 项目结构

## 📁 整理后的文件结构

```
fist/
├── 🚀 部署相关
│   ├── deploy.sh                       # 统一部署管理脚本 (生产)
│   ├── docker-compose.yml              # Docker基础配置
│   ├── docker-compose.override.yml     # 环境特定配置
│   ├── docker-compose.override.yml.example  # 配置示例
│   ├── Dockerfile                      # 容器构建文件
│   └── nginx.conf                      # Nginx配置
│
├── 📖 文档
│   ├── README.md                       # 项目说明
│   ├── DEPLOYMENT.md                   # 快速部署指南
│   ├── PRODUCTION_GUIDE.md             # 生产环境详细指南
│   ├── PROJECT_STRUCTURE.md            # 项目结构说明 (本文件)
│   └── docs/
│       └── DEPENDENCY_MANAGEMENT.md    # 依赖管理指南
│
├── 🏗️ 核心应用
│   ├── app.py                          # 主应用入口
│   ├── pyproject.toml                  # 项目配置和依赖
│   └── uv.lock                         # 依赖锁定文件
│
├── 🔧 核心模块 (core/)
│   ├── __init__.py
│   ├── auth.py                         # 认证和授权
│   ├── config.py                       # 配置管理
│   ├── database.py                     # 数据库连接和操作
│   ├── models.py                       # 数据模型定义
│   ├── moderation.py                   # 内容审核核心逻辑
│   └── type_adapters.py                # 类型转换适配器
│
├── 🛣️ API路由 (routes/)
│   ├── __init__.py
│   ├── admin_routes.py                 # 管理员API
│   ├── api_routes.py                   # 主要API接口
│   └── user_routes.py                  # 用户管理API
│
├── 🤖 AI处理模块 (ai/)
│   ├── __init__.py
│   ├── ai_connector.py                 # AI服务连接器
│   ├── content_processor.py            # 内容处理器
│   ├── cultural_analyzer.py            # 文化分析器
│   ├── feedback_system.py              # 反馈系统
│   ├── language_detector.py            # 语言检测
│   ├── minimal_analyzer.py             # 最小化分析器
│   ├── ml_models.py                    # 机器学习模型
│   ├── multilingual_processor.py       # 多语言处理器
│   ├── semantic_cache.py               # 语义缓存
│   ├── sentiment_analyzer.py           # 情感分析
│   ├── text_analyzer.py                # 文本分析
│   ├── threshold_manager.py            # 阈值管理
│   └── topic_extractor.py              # 主题提取
│
├── 🛠️ 工具模块 (utils/)
│   ├── __init__.py
│   ├── background_tasks.py             # 后台任务
│   ├── batch_processor.py              # 批处理器
│   ├── cache.py                        # 缓存工具
│   └── monitoring.py                   # 监控工具
│
└── 📊 数据文件
    └── fist.db                         # SQLite数据库文件 (开发用)
```

## 🎯 整理成果

### ✅ 已移除的冗余文件

**脚本文件 (8个 → 1个)**:
- ❌ `docker-start.sh` (功能合并到 `deploy.sh`)
- ❌ `config-manager.sh` (功能合并到 `deploy.sh`)
- ❌ `merge-config.sh` (功能合并到 `deploy.sh`)
- ❌ `setup-api-key.sh` (功能合并到 `deploy.sh`)
- ❌ `scripts/docker_restart.sh` (功能合并到 `deploy.sh`)
- ❌ `scripts/check_compatibility.py` (开发/测试用，已移除)
- ❌ `scripts/check_data_types.py` (开发/测试用，已移除)
- ❌ `scripts/reset_database.py` (开发/测试用，已移除)
- ✅ `deploy.sh` (统一的生产部署脚本)

**文档文件 (7个 → 4个)**:
- ❌ `CONFIG_MANAGEMENT.md` (内容合并到 `PRODUCTION_GUIDE.md`)
- ❌ `DOCKER_FOCUSED_SUMMARY.md` (内容合并到 `PRODUCTION_GUIDE.md`)
- ❌ `DOCKER_TROUBLESHOOTING.md` (内容合并到 `PRODUCTION_GUIDE.md`)
- ❌ `docs/DEPLOYMENT.md` (重复文档，已移除)
- ✅ `README.md` (项目说明)
- ✅ `DEPLOYMENT.md` (简化的快速部署指南)
- ✅ `PRODUCTION_GUIDE.md` (详细的生产环境指南)
- ✅ `docs/DEPENDENCY_MANAGEMENT.md` (依赖管理指南)

### 🚀 新的统一部署脚本

`deploy.sh` 集成了以下功能：

```bash
./deploy.sh start          # 启动服务
./deploy.sh restart        # 重启服务 (完全重建)
./deploy.sh stop           # 停止服务
./deploy.sh status         # 查看服务状态
./deploy.sh logs           # 查看服务日志
./deploy.sh setup-api      # 设置API密钥
./deploy.sh init [env]     # 初始化环境配置 (dev|prod|test)
./deploy.sh backup         # 备份当前配置
./deploy.sh validate       # 验证配置
./deploy.sh help           # 显示帮助信息
```

### 📖 精简的文档结构

1. **README.md** - 项目概述和快速开始
2. **DEPLOYMENT.md** - 简化的部署指南，指向详细文档
3. **PRODUCTION_GUIDE.md** - 完整的生产环境部署和管理指南
4. **docs/DEPENDENCY_MANAGEMENT.md** - 依赖管理专门指南

## 🎉 整理效果

### 优势

1. **精简高效**: 脚本文件从8个减少到1个，功能更集中
2. **易于维护**: 统一的部署脚本，减少维护成本
3. **生产就绪**: 专注于生产环境需求，移除开发/测试脚本
4. **文档清晰**: 文档结构更清晰，避免重复内容
5. **用户友好**: 单一入口点，命令更直观

### 使用建议

1. **快速开始**: 查看 `DEPLOYMENT.md`
2. **生产部署**: 参考 `PRODUCTION_GUIDE.md`
3. **日常管理**: 使用 `./deploy.sh` 命令
4. **依赖问题**: 查看 `docs/DEPENDENCY_MANAGEMENT.md`

## 🔄 后续维护

- 所有部署相关功能统一在 `deploy.sh` 中维护
- 文档更新集中在4个主要文档中
- 新功能优先考虑集成到现有脚本而非创建新文件
- 保持项目结构的精简和清晰
