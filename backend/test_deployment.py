#!/usr/bin/env python3
"""Test script to verify backend deployment is working correctly."""

import requests
import json
import sys
import os

def test_backend_health():
    """Test if the backend is responding to health checks."""
    base_url = os.getenv("BACKEND_URL", "https://videosplice.onrender.com")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        print(f"Health check response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_cors_headers():
    """Test if CORS headers are properly configured."""
    base_url = os.getenv("BACKEND_URL", "https://videosplice.onrender.com")
    
    try:
        # Test OPTIONS request (preflight)
        response = requests.options(f"{base_url}/api/status/test-job-id", timeout=10)
        print(f"CORS preflight status: {response.status_code}")
        
        # Check for required CORS headers
        cors_headers = [
            'access-control-allow-origin',
            'access-control-allow-methods',
            'access-control-allow-headers'
        ]
        
        missing_headers = []
        for header in cors_headers:
            if header not in response.headers:
                missing_headers.append(header)
        
        if missing_headers:
            print(f"❌ Missing CORS headers: {missing_headers}")
            return False
        else:
            print("✅ All required CORS headers present")
            return True
            
    except Exception as e:
        print(f"CORS test failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint."""
    base_url = os.getenv("BACKEND_URL", "https://videosplice.onrender.com")
    
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Root endpoint status: {response.status_code}")
        print(f"Root endpoint response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Root endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing VideoSplice backend deployment...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_backend_health),
        ("CORS Headers", test_cors_headers),
        ("Root Endpoint", test_root_endpoint),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            print(f"✅ {test_name} passed")
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n{'=' * 50}")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the backend deployment.")
        sys.exit(1) 