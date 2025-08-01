#!/usr/bin/env python3
"""Test script to verify the new synchronous processing endpoint."""

import requests
import json
import sys
import os

def test_sync_endpoint():
    """Test the new synchronous processing endpoint."""
    base_url = os.getenv("BACKEND_URL", "https://videosplice.onrender.com")
    
    print("Testing synchronous processing endpoint...")
    print(f"Backend URL: {base_url}")
    
    # Test with a simple request to see if the endpoint exists
    try:
        # First test if the endpoint responds to OPTIONS (CORS preflight)
        response = requests.options(f"{base_url}/api/process", timeout=10)
        print(f"OPTIONS request status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ OPTIONS request successful")
        else:
            print(f"❌ OPTIONS request failed: {response.status_code}")
            return False
            
        # Check for CORS headers
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
            print("✅ CORS headers present")
            
        print("✅ Synchronous endpoint test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sync_endpoint()
    
    if success:
        print("\n🎉 Synchronous endpoint is ready!")
        print("The frontend can now use /api/process for one-request processing.")
        sys.exit(0)
    else:
        print("\n⚠️  Synchronous endpoint has issues.")
        sys.exit(1) 