#!/usr/bin/env python3
"""Test script to verify backend.app import works from root directory."""

import sys
from pathlib import Path

def test_backend_import():
    """Test that backend.app can be imported from root directory."""
    try:
        # Add the current directory to Python path
        sys.path.insert(0, str(Path.cwd()))
        
        # Try to import the app
        from backend.app import app
        print("✅ Successfully imported backend.app from root directory")
        print(f"✅ App title: {app.title}")
        return True
    except Exception as e:
        print(f"❌ Failed to import backend.app: {e}")
        return False

if __name__ == "__main__":
    print("Testing backend.app import from root directory...")
    success = test_backend_import()
    if success:
        print("🎉 Import test passed!")
    else:
        print("💥 Import test failed!") 