#!/usr/bin/env python3
"""
FIST 部署检查脚本
检查系统是否准备好部署
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

def check_python_version():
    """检查 Python 版本"""
    print("🐍 检查 Python 版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要 Python 3.8 或更高版本")
        return False

def check_dependencies():
    """检查依赖文件"""
    print("📦 检查依赖文件...")
    
    required_files = [
        "pyproject.toml",
        "uv.lock",
        ".env.example"
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} 缺失")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_env_file():
    """检查环境变量文件"""
    print("⚙️  检查环境变量配置...")
    
    if not Path(".env").exists():
        print("   ⚠️  .env 文件不存在")
        print("   请复制 .env.example 到 .env 并配置")
        return False
    
    print("   ✅ .env 文件存在")
    
    # 检查关键环境变量
    required_vars = [
        "SECRET_KEY",
        "ADMIN_PASSWORD",
        "DATABASE_URL"
    ]
    
    missing_vars = []
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        for var in required_vars:
            value = os.getenv(var)
            if value and value != f"your-{var.lower().replace('_', '-')}-here":
                print(f"   ✅ {var}")
            else:
                print(f"   ❌ {var} 未配置或使用默认值")
                missing_vars.append(var)
    except ImportError:
        print("   ⚠️  无法检查环境变量 (python-dotenv 未安装)")
        return True
    
    return len(missing_vars) == 0

def check_database():
    """检查数据库连接"""
    print("🗄️  检查数据库连接...")
    
    try:
        from core.database import get_db
        next(get_db())
        print("   ✅ 数据库连接正常")
        return True
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        return False

def check_imports():
    """检查关键模块导入"""
    print("📚 检查模块导入...")
    
    try:
        from core import get_moderation_service
        print("   ✅ 核心模块导入正常")
        
        from app import app
        print("   ✅ FastAPI 应用导入正常")
        
        return True
    except Exception as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False

def check_docker():
    """检查 Docker 环境"""
    print("🐳 检查 Docker 环境...")
    
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"   ✅ {result.stdout.strip()}")
        
        result = subprocess.run(["docker-compose", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"   ✅ {result.stdout.strip()}")
        
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ⚠️  Docker 或 Docker Compose 未安装")
        print("   如果不使用 Docker 部署，可以忽略此警告")
        return True

def check_api_health(url="http://localhost:8000"):
    """检查 API 健康状态"""
    print(f"🌐 检查 API 健康状态 ({url})...")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("   ✅ API 响应正常")
            return True
        else:
            print(f"   ❌ API 响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  无法连接到 API: {e}")
        print("   如果服务未启动，这是正常的")
        return True

def run_basic_test():
    """运行基本功能测试"""
    print("🧪 运行基本功能测试...")
    
    try:
        from core import get_moderation_service
        service = get_moderation_service()
        
        # 测试内容处理
        result = service.pierce_content("这是一个测试内容")
        if result and len(result) == 2:
            print("   ✅ 内容处理功能正常")
            return True
        else:
            print("   ❌ 内容处理功能异常")
            return False
    except Exception as e:
        print(f"   ❌ 基本功能测试失败: {e}")
        return False

def main():
    """主检查函数"""
    print("🚀 FIST 部署检查开始")
    print("=" * 50)
    
    checks = [
        ("Python 版本", check_python_version),
        ("依赖文件", check_dependencies),
        ("环境变量", check_env_file),
        ("模块导入", check_imports),
        ("数据库连接", check_database),
        ("基本功能", run_basic_test),
        ("Docker 环境", check_docker),
        ("API 健康", check_api_health),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {name} 检查出错: {e}")
        print()
    
    print("=" * 50)
    print(f"📊 检查结果: {passed}/{total} 项通过")
    
    if passed == total:
        print("🎉 所有检查通过！系统准备就绪")
        print("\n🚀 部署建议:")
        print("   1. 确保生产环境变量已正确配置")
        print("   2. 使用 docker-compose up -d 启动服务")
        print("   3. 访问 http://localhost:8000/docs 查看 API 文档")
        return 0
    elif passed >= total - 2:
        print("⚠️  大部分检查通过，可以尝试部署")
        print("   请注意解决失败的检查项")
        return 0
    else:
        print("❌ 多项检查失败，请解决问题后再部署")
        return 1

if __name__ == "__main__":
    sys.exit(main())
