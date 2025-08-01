#!/usr/bin/env bash
# Render start script for VideoSplice backend

PORT=${PORT:-8000}

# Create necessary directories
mkdir -p ../data/uploads
mkdir -p outputs
mkdir -p runs

# Set Python path to include the current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the application
exec uvicorn backend.app:app --host 0.0.0.0 --port "$PORT" --workers 1
