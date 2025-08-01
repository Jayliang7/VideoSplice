#!/usr/bin/env bash
# Render start script for VideoSplice backend

PORT=${PORT:-8000}

# Create necessary directories
mkdir -p ../data/uploads
mkdir -p outputs
mkdir -p runs

# NOTE: app.py lives in backend/, so we import it as backend.app
exec uvicorn app:app --host 0.0.0.0 --port "$PORT" --workers 1
