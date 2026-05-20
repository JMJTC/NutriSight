#!/bin/sh
set -e

# Start nginx in background (serves frontend + proxies /api/)
nginx

# Start FastAPI in foreground (Docker tracks this process for health/signals)
exec python run.py
