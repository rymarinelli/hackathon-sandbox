#!/usr/bin/env sh
set -euo pipefail

HOST=${APP_HOST:-0.0.0.0}
PORT=${APP_PORT:-8000}

exec uvicorn gateway.main:app --host "$HOST" --port "$PORT" --proxy-headers --forwarded-allow-ips "*"
