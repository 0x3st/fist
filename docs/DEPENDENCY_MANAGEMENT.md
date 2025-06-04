# 📦 依赖管理指南

## 🎯 概述

FIST 系统使用现代化的依赖管理策略，确保所有组件的版本兼容性和安全性。

## 📋 核心依赖版本

### 🔧 **核心框架**
- **Python**: 3.13+ (必需)
- **FastAPI**: 0.100.0+ < 1.0.0
- **Uvicorn**: 0.20.0+ < 1.0.0
- **Pydantic**: 2.0.0+ < 3.0.0 (支持 `model_dump()`)
- **SQLAlchemy**: 2.0.0+ < 3.0.0 (现代异步API)

### 🔐 **安全认证**
- **python-jose**: 3.3.0+ (JWT处理)
- **passlib**: 1.7.0+ (密码哈希)
- **bcrypt**: 4.0.1 (固定版本，安全考虑)

### 🤖 **AI/ML 组件**
- **OpenAI**: 1.0.0+ (官方客户端)
- **Transformers**: 4.20.0+ (HuggingFace)
- **PyTorch**: 2.0.0+ (深度学习框架)
- **spaCy**: 3.4.0+ (NLP处理)
- **scikit-learn**: 1.1.0+ (机器学习)

## 🔍 兼容性检查

### 自动检查脚本
```bash
# 运行兼容性检查
python scripts/check_compatibility.py

# 检查特定包
python -c "import pydantic; print(f'Pydantic: {pydantic.__version__}')"
```

### 手动验证
```python
# 验证 Pydantic v2 功能
from pydantic import BaseModel
class TestModel(BaseModel):
    name: str

model = TestModel(name="test")
data = model.model_dump()  # 应该工作正常
```

## 🔄 更新策略

### 1. **安全更新** (立即应用)
```bash
# 更新安全补丁
uv sync --upgrade-package bcrypt
uv sync --upgrade-package cryptography
```

### 2. **次要版本更新** (定期应用)
```bash
# 更新所有依赖到兼容版本
uv sync --upgrade

# 更新特定包
uv add "fastapi>=0.110.0,<1.0.0"
```

### 3. **主要版本更新** (谨慎测试)
```bash
# 测试环境先更新
uv add "pydantic>=3.0.0,<4.0.0" --dev

# 运行完整测试套件
python -m pytest tests/

# 兼容性检查
python scripts/check_compatibility.py
```

## ⚠️ 已知兼容性问题

### 1. **Pydantic v1 → v2 迁移**
- ❌ **问题**: `.dict()` 方法已弃用
- ✅ **解决**: 使用 `.model_dump()` 方法
- 📝 **代码示例**:
```python
# 旧版本 (Pydantic v1)
data = model.dict()

# 新版本 (Pydantic v2)
data = model.model_dump()
```

### 2. **SQLAlchemy 1.x → 2.0 迁移**
- ❌ **问题**: 查询语法变化
- ✅ **解决**: 使用新的查询API
- 📝 **代码示例**:
```python
# 旧版本 (SQLAlchemy 1.x)
from sqlalchemy.orm import Query
result = session.query(Model).filter(Model.id == 1).first()

# 新版本 (SQLAlchemy 2.0)
from sqlalchemy import select
result = session.execute(select(Model).where(Model.id == 1)).scalar_one_or_none()
```

### 3. **FastAPI 版本兼容性**
- ✅ **当前**: 使用 FastAPI 0.115.x
- 📌 **注意**: 1.0.0 版本可能有破坏性变更
- 🔒 **策略**: 版本约束 `<1.0.0`

## 🛠️ 故障排除

### 版本冲突解决
```bash
# 清理依赖缓存
uv cache clean

# 重新安装所有依赖
rm uv.lock
uv sync

# 检查依赖树
uv tree
```

### 常见错误修复

#### 1. **ImportError: cannot import name 'model_dump'**
```bash
# 升级 Pydantic 到 v2
uv add "pydantic>=2.0.0,<3.0.0"
```

#### 2. **AttributeError: 'Query' object has no attribute 'scalar_one'**
```bash
# 升级 SQLAlchemy 到 v2
uv add "sqlalchemy>=2.0.0,<3.0.0"
```

#### 3. **ModuleNotFoundError: No module named 'fastapi.encoders'**
```bash
# 检查 FastAPI 版本
uv add "fastapi>=0.100.0,<1.0.0"
```

## 📊 依赖监控

### 定期检查清单
- [ ] 每月运行兼容性检查
- [ ] 监控安全漏洞报告
- [ ] 测试新版本兼容性
- [ ] 更新文档和示例代码

### 自动化工具
```bash
# 安全漏洞扫描
uv audit

# 过时包检查
uv outdated

# 依赖分析
uv show --tree
```

## 🔮 未来规划

### 即将到来的变更
1. **FastAPI 1.0**: 准备迁移计划
2. **Pydantic v3**: 评估新功能
3. **Python 3.14**: 测试兼容性

### 长期策略
- 保持依赖版本的现代化
- 优先考虑安全性和稳定性
- 渐进式升级，避免大规模重构
