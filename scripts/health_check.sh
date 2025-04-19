#!/usr/bin/env bash
set -euo pipefail

# 1) wacht tot Nginx/Gunicorn up is (max 30s)
for i in {1..30}; do
  if ss -tulpn | grep -q ':80 '; then
    break
  fi
  sleep 1
done

# 2) pingen met exact de hostnaam uit ALLOWED_HOSTS
curl --fail \
     --resolve doc-gen.eu:80:127.0.0.1 \
     http://doc-gen.eu/health/
