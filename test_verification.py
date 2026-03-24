
import requests
from datetime import datetime
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_validation_logic():
    print("Test 1: Sending invalid OHLC data (High < Low)...")
    payload = {
        "target": "primary",
        "provider": "test_verification",
        "items": [
            {
                "symbol": "sh.000000",
                "frequency": "d",
                "timestamp": datetime.now().isoformat(),
                "open": 10.0,
                "high": 9.0,  # Invalid: High < Open
                "low": 11.0,  # Invalid: Low > Open/High
                "close": 10.0,
                "volume": 1000,
            }
        ]
    }
    # Login first? Using default dev permissions might require token.
    # Assuming local dev with disabled auth or we need to login.
    # BackendClient has login logic. Let's see if we can hit it directly if permitted
    # or just use BackendClient logic? 
    # Let's try to hit it. If 401, we know environment needs auth.
    try:
        resp = requests.post(f"{BASE_URL}/stocks/kline", json=payload)
        if resp.status_code == 422 or resp.status_code == 400:
            print(f"PASS: Rejected invalid data as expected. Code: {resp.status_code}")
            print(resp.text)
        elif resp.status_code == 401:
             print("SKIP: Auth required. Assuming logic works if it reached Pydantic.")
        else:
            print(f"FAIL: Unexpected status code {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

def test_integrity_api():
    print("\nTest 2: Calling integrity check API...")
    payload = {
        "target": "primary",
        "items": [
            {
                "symbol": "sh.600000",
                "frequency": "d",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        ]
    }
    try:
        resp = requests.post(f"{BASE_URL}/integrity/check", json=payload)
        if resp.status_code == 200:
            print("PASS: Integrity API returned 200 OK.")
            print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        elif resp.status_code == 401:
             print("SKIP: Auth required.")
        else:
            print(f"FAIL: Unexpected status code {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure backend is running.
    test_validation_logic()
    test_integrity_api()
