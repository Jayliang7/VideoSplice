#!/usr/bin/env python3
"""Test script to verify CORS headers are working correctly."""

import requests
import json
import os

def test_cors_headers():
    """Test that CORS headers are present in responses."""
    base_url = os.getenv("BACKEND_URL", "https://videosplice.onrender.com")
    
    # Test OPTIONS request (preflight)
    try:
        response = requests.options(f"{base_url}/api/status/test-job-id")
        print(f"OPTIONS request status: {response.status_code}")
        print(f"CORS headers: {dict(response.headers)}")
        
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
        print(f"❌ CORS test failed: {e}")
        return False

def test_actual_request():
    """Test actual GET request with CORS headers."""
    base_url = os.getenv("BACKEND_URL", "https://videosplice.onrender.com")
    
    try:
        response = requests.get(f"{base_url}/health")
        print(f"GET request status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Check for CORS headers in GET response
        if 'access-control-allow-origin' in response.headers:
            print("✅ CORS headers present in GET response")
            return True
        else:
            print("❌ CORS headers missing in GET response")
            return False
            
    except Exception as e:
        print(f"❌ GET request test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing CORS configuration...")
    print("--- CORS Headers Test ---")
    cors_result = test_cors_headers()
    
    print("\n--- GET Request Test ---")
    get_result = test_actual_request()
    
    print(f"\nResults: {sum([cors_result, get_result])}/2 tests passed")
    
    if cors_result and get_result:
        print("✅ CORS configuration is working correctly!")
    else:
        print("❌ CORS configuration has issues") 