#!/bin/zsh
set -euo pipefail

BACKEND_DIR="/Users/123ang/andai-runtime/local_llm/backend"
FRONTEND_DIR="/Users/123ang/andai-runtime/local_llm/frontend"
LOG_DIR="/Users/123ang/andai-runtime/local_llm/deploy/launchd"

mkdir -p "$LOG_DIR"

# backend: uvicorn on 8000
if ! /usr/sbin/lsof -tiTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  /usr/bin/osascript <<'APPLESCRIPT'
tell application "Terminal"
  do script "cd /Users/123ang/andai-runtime/local_llm/backend && ./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
end tell
APPLESCRIPT
fi

# frontend: next start on 3000 (requires built app)
if ! /usr/sbin/lsof -tiTCP:3000 -sTCP:LISTEN >/dev/null 2>&1; then
  /usr/bin/osascript <<'APPLESCRIPT'
tell application "Terminal"
  do script "cd /Users/123ang/andai-runtime/local_llm/frontend && NEXT_TELEMETRY_DISABLED=1 CI=1 ./node_modules/.bin/next start --hostname 127.0.0.1 --port 3000"
end tell
APPLESCRIPT
fi
