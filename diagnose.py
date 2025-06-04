#!/usr/bin/env python3
"""
FIST 应用诊断脚本
用于检查应用启动时可能遇到的问题
"""

import os
import sys
import traceback

def check_environment():
    """检查环境变量"""
    print("🔍 检查环境变量...")
    
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY", 
        "ADMIN_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 不显示敏感信息的完整值
            if var in ["SECRET_KEY", "ADMIN_PASSWORD", "AI_API_KEY"]:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"   ✅ {var} = {display_value}")
        else:
            print(f"   ❌ {var} 未设置")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def check_imports():
    """检查关键模块导入"""
    print("\n📚 检查模块导入...")
    
    modules_to_check = [
        ("fastapi", "FastAPI"),
        ("sqlalchemy", "SQLAlchemy"),
        ("uvicorn", "Uvicorn"),
        ("core.config", "Config"),
        ("core.database", "Database"),
        ("core.models", "Models"),
    ]
    
    failed_imports = []
    
    for module_name, display_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"   ✅ {display_name}")
        except ImportError as e:
            print(f"   ❌ {display_name}: {e}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0

def check_database():
    """检查数据库连接"""
    print("\n🗄️ 检查数据库连接...")
    
    try:
        from core.config import Config
        from core.database import engine, SessionLocal
        from sqlalchemy import text
        
        print(f"   📍 数据库URL: {Config.DATABASE_URL}")
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("   ✅ 数据库连接成功")
        
        # 测试会话
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("   ✅ 数据库会话正常")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        print(f"   📋 错误详情: {traceback.format_exc()}")
        return False

def check_app_creation():
    """检查FastAPI应用创建"""
    print("\n🚀 检查FastAPI应用创建...")
    
    try:
        from app import app
        print("   ✅ FastAPI应用创建成功")
        print(f"   📍 应用标题: {app.title}")
        print(f"   📍 应用版本: {app.version}")
        return True
        
    except Exception as e:
        print(f"   ❌ FastAPI应用创建失败: {e}")
        print(f"   📋 错误详情: {traceback.format_exc()}")
        return False

def check_routes():
    """检查路由加载"""
    print("\n🛣️ 检查路由加载...")
    
    try:
        from routes import api_routes, user_routes, admin_routes
        print("   ✅ API路由加载成功")
        print("   ✅ 用户路由加载成功") 
        print("   ✅ 管理员路由加载成功")
        return True
        
    except Exception as e:
        print(f"   ❌ 路由加载失败: {e}")
        print(f"   📋 错误详情: {traceback.format_exc()}")
        return False

def main():
    """主诊断函数"""
    print("🔧 FIST 应用诊断开始")
    print("=" * 50)
    
    checks = [
        ("环境变量", check_environment),
        ("模块导入", check_imports),
        ("数据库连接", check_database),
        ("应用创建", check_app_creation),
        ("路由加载", check_routes),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {name} 检查出错: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 诊断结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("🎉 所有检查通过！应用应该可以正常启动")
        return 0
    else:
        print("⚠️ 发现问题，请根据上述错误信息进行修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())
