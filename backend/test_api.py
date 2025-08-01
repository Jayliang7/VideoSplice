#!/usr/bin/env python3
"""Simple test script to verify API endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_root():
    """Test the root endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Root endpoint: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Root endpoint failed: {e}")
        return False

def test_cors():
    """Test CORS headers."""
    try:
        response = requests.options(f"{BASE_URL}/api/upload")
        print(f"CORS headers: {dict(response.headers)}")
        return "access-control-allow-origin" in response.headers
    except Exception as e:
        print(f"CORS test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing VideoSplice API...")
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("CORS Headers", test_cors),
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        if test_func():
            passed += 1
            print(f"✅ {name} PASSED")
        else:
            print(f"❌ {name} FAILED")
    
    print(f"\nResults: {passed}/{len(tests)} tests passed") 