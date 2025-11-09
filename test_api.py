#!/usr/bin/env python3
"""
简单的API测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_health():
    """测试健康检查"""
    response = requests.get("http://localhost:8000/health")
    print(f"健康检查: {response.status_code} - {response.json()}")


def test_register():
    """测试用户注册"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123",
        "full_name": "测试用户",
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"用户注册: {response.status_code} - {response.json()}")


def test_login():
    """测试用户登录"""
    login_data = {"username": "testuser", "password": "test123"}
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    print(f"用户登录: {response.status_code} - {response.json()}")
    return response.json().get("access_token") if response.status_code == 200 else None


def test_indicators(token=None):
    """测试指标API"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 测试获取股票列表
    response = requests.get(f"{BASE_URL}/indicators/stocks", headers=headers)
    print(f"获取股票列表: {response.status_code}")

    # 测试获取市场概览
    response = requests.get(f"{BASE_URL}/indicators/market/overview", headers=headers)
    print(f"获取市场概览: {response.status_code}")


def test_strategies(token):
    """测试策略API"""
    headers = {"Authorization": f"Bearer {token}"}

    # 测试创建策略
    strategy_data = {
        "name": "测试策略",
        "description": "这是一个测试策略",
        "is_public": True,
        "strategy_type": "momentum",
        "parameters": {"period": 20, "threshold": 0.05},
    }
    response = requests.post(
        f"{BASE_URL}/strategies/", json=strategy_data, headers=headers
    )
    print(f"创建策略: {response.status_code} - {response.json()}")


def test_qlib_data_ingest(token):
    """测试qlib数据接入接口"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "provider": "test-feed",
        "market": "cn",
        "records": [
            {
                "instrument": "SH600519",
                "datetime": "2024-10-08T15:00:00+08:00",
                "freq": "1d",
                "open": 1600.5,
                "high": 1611.2,
                "low": 1590.0,
                "close": 1605.4,
                "volume": 123456,
                "amount": 987654321,
                "factor": 1.0,
                "turnover": 0.35,
                "limit_status": "none",
                "suspended": False,
                "extra_fields": {"Ref(close,1)": 1588.1},
            }
        ],
    }
    response = requests.post(
        f"{BASE_URL}/data/qlib/bars", json=payload, headers=headers
    )
    print(f"推送qlib数据: {response.status_code} - {response.json()}")


def main():
    """主测试函数"""
    print("开始API测试...")

    # 测试健康检查
    test_health()

    # 测试用户注册
    test_register()

    # 测试用户登录
    token = test_login()

    # 测试指标API（无需认证）
    test_indicators()

    if token:
        # 测试策略API（需要认证）
        test_strategies(token)
        test_qlib_data_ingest(token)

    print("API测试完成！")


if __name__ == "__main__":
    main()
