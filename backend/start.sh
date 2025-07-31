#!/usr/bin/env bash
# -------------------------------------------
# Render start script for VideoSplice backend
# -------------------------------------------

# Use the PORT provided by Render, default 8000 when running locally
PORT=${PORT:-8000}

# Start Uvicorn
exec uvicorn app:app --host 0.0.0.0 --port "$PORT"