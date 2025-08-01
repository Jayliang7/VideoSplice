#!/usr/bin/env python3
"""Test script to verify backend startup without HF API token."""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test that all modules can be imported without errors."""
    try:
        print("Testing imports...")
        
        # Test basic imports
        import app
        print("✅ app.py imported successfully")
        
        # Test video pipeline imports
        from video_pipeline import config
        print("✅ config.py imported successfully")
        
        # Test pipeline import (this might fail without HF token)
        try:
            from video_pipeline import pipeline
            print("✅ pipeline.py imported successfully")
        except Exception as e:
            print(f"⚠️  pipeline.py import failed (expected without HF token): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    try:
        from video_pipeline import config
        print(f"✅ Config loaded - HF_API_TOKEN: {'Set' if config.HF_API_TOKEN else 'Not set'}")
        print(f"✅ RUNS_ROOT: {config.RUNS_ROOT}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing VideoSplice backend startup...")
    
    tests = [
        ("Import Test", test_imports),
        ("Config Test", test_config),
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
    
    if passed == len(tests):
        print("🎉 Backend should start successfully!")
    else:
        print("⚠️  Some issues detected, but backend may still work") 