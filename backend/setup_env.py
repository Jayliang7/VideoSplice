#!/usr/bin/env python3
"""Script to help set up environment variables for deployment."""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if required environment variables are set."""
    print("Checking environment variables...")
    
    # Required for basic functionality
    required_vars = []
    
    # Optional but recommended
    optional_vars = [
        ("HF_API_TOKEN", "Hugging Face API token for frame labeling"),
        ("HF_API_URL", "Hugging Face API URL (optional, has default)"),
    ]
    
    print("\nRequired environment variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (set)")
        else:
            print(f"❌ {var}: Not set")
    
    print("\nOptional environment variables:")
    for var, description in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (set) - {description}")
        else:
            print(f"⚠️  {var}: Not set - {description}")
    
    # Check if .env file exists
    repo_root = Path(__file__).resolve().parent.parent
    env_file = repo_root / ".env"
    
    print(f"\nEnvironment file:")
    if env_file.exists():
        print(f"✅ .env file exists at {env_file}")
    else:
        print(f"⚠️  .env file not found at {env_file}")
        print("   Create one with your environment variables if needed.")

def create_env_template():
    """Create a template .env file."""
    repo_root = Path(__file__).resolve().parent.parent
    env_file = repo_root / ".env"
    
    if env_file.exists():
        print(f"⚠️  .env file already exists at {env_file}")
        return
    
    template = """# VideoSplice Environment Variables
# Copy this file to .env and fill in your values

# Hugging Face API Configuration (optional)
# Get your token from https://huggingface.co/settings/tokens
HF_API_TOKEN=your_huggingface_token_here

# Hugging Face API URL (optional, has default)
# HF_API_URL=https://your-custom-endpoint.com/pipeline/feature-extraction/openai/clip-vit-base-patch32

# Backend URL for testing (optional)
# BACKEND_URL=https://videosplice.onrender.com
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(template)
        print(f"✅ Created .env template at {env_file}")
        print("   Edit the file and add your actual values.")
    except Exception as e:
        print(f"❌ Failed to create .env template: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        create_env_template()
    else:
        check_environment()
        print("\nTo create a .env template, run: python setup_env.py create") 