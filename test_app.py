#!/usr/bin/env python3
"""
简单的应用测试脚本
"""

import os
import sys

# 设置环境变量
os.environ["DATABASE_URL"] = "sqlite:///./test_fist.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["ADMIN_PASSWORD"] = "test-admin-password"
os.environ["DEBUG"] = "true"
os.environ["ENABLE_CACHING"] = "false"  # 禁用Redis缓存

def test_app_import():
    """测试应用导入"""
    print("🔍 测试应用导入...")
    
    try:
        from app import app
        print("✅ 应用导入成功")
        return True
    except Exception as e:
        print(f"❌ 应用导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_endpoint():
    """测试健康检查端点"""
    print("\n🔍 测试健康检查端点...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 200:
            print("✅ 健康检查端点正常")
            return True
        else:
            print("❌ 健康检查端点异常")
            return False
            
    except Exception as e:
        print(f"❌ 健康检查测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_root_endpoint():
    """测试根端点"""
    print("\n🔍 测试根端点...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        response = client.get("/")
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 根端点正常")
            return True
        else:
            print(f"❌ 根端点异常: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ 根端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_docs_endpoint():
    """测试文档端点"""
    print("\n🔍 测试文档端点...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        response = client.get("/docs")
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 文档端点正常")
            return True
        else:
            print(f"❌ 文档端点异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 文档端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 FIST 应用测试开始")
    print("=" * 40)
    
    tests = [
        ("应用导入", test_app_import),
        ("健康检查端点", test_health_endpoint),
        ("根端点", test_root_endpoint),
        ("文档端点", test_docs_endpoint),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {name} 测试出错: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 测试结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用可以正常运行")
        return 0
    else:
        print("⚠️ 发现问题，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
