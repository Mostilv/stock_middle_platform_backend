#!/usr/bin/env python3
"""
测试Swagger配置
"""

import requests
import json
from app.main import app

def test_swagger_endpoints():
    """测试Swagger相关端点"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 测试Swagger配置...")
    print("=" * 50)
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ 根路径访问成功")
            data = response.json()
            print(f"   项目名称: {data.get('message', 'N/A')}")
            print(f"   版本: {data.get('version', 'N/A')}")
        else:
            print(f"❌ 根路径访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 根路径测试异常: {e}")
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ 健康检查成功")
            data = response.json()
            print(f"   状态: {data.get('status', 'N/A')}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查测试异常: {e}")
    
    # 测试OpenAPI规范
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            print("✅ OpenAPI规范获取成功")
            data = response.json()
            print(f"   API标题: {data.get('info', {}).get('title', 'N/A')}")
            print(f"   版本: {data.get('info', {}).get('version', 'N/A')}")
            print(f"   标签数量: {len(data.get('tags', []))}")
            print(f"   路径数量: {len(data.get('paths', {}))}")
        else:
            print(f"❌ OpenAPI规范获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenAPI规范测试异常: {e}")
    
    print("=" * 50)
    print("🎯 测试完成！")
    print("📚 访问Swagger UI: http://localhost:8000/docs")
    print("📖 访问ReDoc: http://localhost:8000/redoc")

def test_app_config():
    """测试应用配置"""
    
    print("🔧 测试应用配置...")
    print("=" * 50)
    
    # 测试FastAPI应用配置
    print(f"应用标题: {app.title}")
    print(f"应用版本: {app.version}")
    print(f"调试模式: {app.debug}")
    print(f"文档URL: {app.docs_url}")
    print(f"ReDoc URL: {app.redoc_url}")
    print(f"OpenAPI URL: {app.openapi_url}")
    
    # 测试标签配置
    if hasattr(app, 'openapi_schema') and app.openapi_schema:
        tags = app.openapi_schema.get('tags', [])
        print(f"API标签数量: {len(tags)}")
        for tag in tags:
            print(f"  - {tag.get('name')}: {tag.get('description')}")
    
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 Swagger配置测试工具")
    print("=" * 50)
    
    # 测试应用配置
    test_app_config()
    
    print()
    
    # 测试Swagger端点（需要服务运行）
    print("💡 提示: 要测试Swagger端点，请先启动服务")
    print("   启动命令: python start_swagger.py")
    print("   或: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
    # 询问是否要测试端点
    try:
        choice = input("\n是否要测试Swagger端点？(y/n): ").lower().strip()
        if choice in ['y', 'yes', '是']:
            test_swagger_endpoints()
    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")


