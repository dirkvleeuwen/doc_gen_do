#!/usr/bin/env bash
set -euo pipefail

# even de server laten opstarten
sleep 10

# max 5 pogingen
for i in {1..5}; do
  if curl -fsS http://127.0.0.1:8000/; then
    echo "✅ Healthcheck OK"
    exit 0
  else
    echo "Attempt $i failed, retry in 5s..."
    sleep 5
  fi
done

echo "❌ Healthcheck failed"
exit 1
