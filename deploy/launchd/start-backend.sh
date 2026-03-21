#!/bin/zsh
set -euo pipefail

cd "/Users/123ang/Desktop/Websites/local_llm/backend"
exec "./venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
