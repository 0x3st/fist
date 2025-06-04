# FIST Content Moderation System - 部署指南

## 🎯 概述

FIST (Fast Intelligent Security Text) 是一个基于AI的内容审核系统，支持多种AI服务和高级文本分析功能。

## 🚀 快速部署

### Docker 部署 (推荐)

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd fist

# 2. 设置API密钥
./deploy.sh setup-api

# 3. 初始化生产环境
./deploy.sh init prod

# 4. 启动服务
./deploy.sh start

# 5. 访问服务
# API: http://localhost:8000
# 文档: http://localhost:8000/docs
```

## 📖 详细指南

- **生产环境部署**: 请参考 [生产环境部署指南](PRODUCTION_GUIDE.md)
- **依赖管理**: 请参考 [依赖管理指南](docs/DEPENDENCY_MANAGEMENT.md)

## 🔧 主要命令

```bash
# 查看所有可用命令
./deploy.sh help

# 常用操作
./deploy.sh start      # 启动服务
./deploy.sh stop       # 停止服务
./deploy.sh restart    # 重启服务
./deploy.sh status     # 查看状态
./deploy.sh logs       # 查看日志
./deploy.sh backup     # 备份配置
./deploy.sh validate   # 验证配置
```

## 🔧 服务组件

系统包含以下服务：

- **fist-api**: 主应用服务
- **db**: PostgreSQL 数据库
- **redis**: Redis 缓存

## 🆘 故障排除

### 常见问题

1. **服务启动失败**
```bash
./deploy.sh validate  # 验证配置
./deploy.sh logs      # 查看日志
```

2. **端口冲突**
```bash
./deploy.sh init dev  # 使用开发环境端口
```

3. **API连接问题**
```bash
curl http://localhost:8000/  # 测试连接
./deploy.sh status           # 查看服务状态
```

## 📞 获取帮助

如果遇到部署问题：

1. 查看部署脚本帮助：`./deploy.sh help`
2. 检查服务日志：`./deploy.sh logs`
3. 验证配置：`./deploy.sh validate`
4. 参考详细指南：[生产环境部署指南](PRODUCTION_GUIDE.md)

更多技术支持，请参考项目文档或提交 Issue。
