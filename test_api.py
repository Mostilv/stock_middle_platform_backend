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


def test_indicator_pipeline(token):
    """测试指标推送与查询流程"""
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "provider": "demo-service",
        "records": [
            {
                "symbol": "SH600519",
                "indicator": "rsi14",
                "timeframe": "1d",
                "timestamp": "2024-10-08T15:00:00+08:00",
                "value": 56.2,
                "values": {"overbought": 70, "oversold": 30},
                "payload": {"window": 14},
                "tags": ["demo", "daily"],
            }
        ],
    }
    response = requests.post(
        f"{BASE_URL}/indicators/records", json=payload, headers=headers
    )
    print(f"推送指标数据: {response.status_code} - {response.json()}")

    params = {
        "indicator": "rsi14",
        "symbol": "SH600519",
        "timeframe": "1d",
        "limit": 5,
    }
    response = requests.get(
        f"{BASE_URL}/indicators/records", params=params, headers=headers
    )
    print(f"查询指标数据: {response.status_code} - {response.json()}")


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

    if token:
        # 指标推送与查询（需要认证）
        test_indicator_pipeline(token)
        # 测试策略API（需要认证）
        test_strategies(token)
        test_qlib_data_ingest(token)

    print("API测试完成！")


if __name__ == "__main__":
    main()
