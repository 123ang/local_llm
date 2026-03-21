#!/bin/zsh
set -euo pipefail

exec /opt/homebrew/bin/pnpm --dir "/Users/123ang/Desktop/Websites/local_llm/frontend" dev --hostname 127.0.0.1 --port 3000
