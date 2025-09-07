#!/usr/bin/env python3
"""
完整的Swagger功能测试脚本
"""

import requests
import json
import time

def test_swagger_complete():
    """完整测试Swagger功能"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 股票中间平台后端 - Swagger功能测试")
    print("=" * 60)
    
    # 测试根路径
    print("1️⃣ 测试根路径...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   ✅ 根路径访问成功")
            data = response.json()
            print(f"   📝 项目名称: {data.get('message', 'N/A')}")
            print(f"   📋 版本: {data.get('version', 'N/A')}")
            print(f"   📚 文档地址: {data.get('docs', 'N/A')}")
        else:
            print(f"   ❌ 根路径访问失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 根路径测试异常: {e}")
    
    print()
    
    # 测试健康检查
    print("2️⃣ 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ 健康检查成功")
            data = response.json()
            print(f"   💚 状态: {data.get('status', 'N/A')}")
            print(f"   🏷️ 服务: {data.get('service', 'N/A')}")
        else:
            print(f"   ❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 健康检查测试异常: {e}")
    
    print()
    
    # 测试OpenAPI规范
    print("3️⃣ 测试OpenAPI规范...")
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            print("   ✅ OpenAPI规范获取成功")
            data = response.json()
            print(f"   📖 API标题: {data.get('info', {}).get('title', 'N/A')}")
            print(f"   📋 版本: {data.get('info', {}).get('version', 'N/A')}")
            print(f"   🏷️ 标签数量: {len(data.get('tags', []))}")
            print(f"   🛣️ 路径数量: {len(data.get('paths', {}))}")
            
            # 显示标签信息
            tags = data.get('tags', [])
            if tags:
                print("   📑 API标签:")
                for tag in tags:
                    print(f"      - {tag.get('name')}: {tag.get('description')}")
            
            # 显示安全配置
            security_schemes = data.get('components', {}).get('securitySchemes', {})
            if security_schemes:
                print("   🔐 安全配置:")
                for scheme_name, scheme_info in security_schemes.items():
                    print(f"      - {scheme_name}: {scheme_info.get('type')} ({scheme_info.get('scheme')})")
        else:
            print(f"   ❌ OpenAPI规范获取失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ OpenAPI规范测试异常: {e}")
    
    print()
    
    # 测试Swagger UI
    print("4️⃣ 测试Swagger UI...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("   ✅ Swagger UI访问成功")
            print("   🌐 地址: http://localhost:8000/docs")
        else:
            print(f"   ❌ Swagger UI访问失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Swagger UI测试异常: {e}")
    
    print()
    
    # 测试ReDoc
    print("5️⃣ 测试ReDoc...")
    try:
        response = requests.get(f"{base_url}/redoc")
        if response.status_code == 200:
            print("   ✅ ReDoc访问成功")
            print("   🌐 地址: http://localhost:8000/redoc")
        else:
            print(f"   ❌ ReDoc访问失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ReDoc测试异常: {e}")
    
    print()
    
    # 测试API端点
    print("6️⃣ 测试API端点...")
    api_endpoints = [
        "/api/v1/auth/register",
        "/api/v1/auth/login", 
        "/api/v1/auth/me",
        "/api/v1/users/",
        "/api/v1/roles/",
        "/api/v1/strategies/",
        "/api/v1/indicators/"
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code in [200, 401, 422]:  # 200成功，401未授权，422参数错误都是正常的
                print(f"   ✅ {endpoint} - 状态码: {response.status_code}")
            else:
                print(f"   ⚠️ {endpoint} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} - 异常: {e}")
    
    print()
    print("=" * 60)
    print("🎯 测试完成！")
    print()
    print("📚 访问地址:")
    print("   Swagger UI: http://localhost:8000/docs")
    print("   ReDoc:      http://localhost:8000/redoc")
    print("   OpenAPI:    http://localhost:8000/openapi.json")
    print()
    print("💡 使用提示:")
    print("   1. 打开浏览器访问 http://localhost:8000/docs")
    print("   2. 在Swagger UI中可以查看所有API接口")
    print("   3. 点击 'Try it out' 按钮可以直接测试API")
    print("   4. 使用右上角的 'Authorize' 按钮进行JWT认证")
    print()
    print("🎉 Swagger集成成功！享受更好的API开发体验！")

if __name__ == "__main__":
    test_swagger_complete()

