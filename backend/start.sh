#!/usr/bin/env bash
# Render start script for VideoSplice backend

PORT=${PORT:-8000}

# NOTE: app.py lives in backend/, so we import it as backend.app
exec uvicorn backend.app:app --host 0.0.0.0 --port "$PORT"
