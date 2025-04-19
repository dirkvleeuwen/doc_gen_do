#!/usr/bin/env bash
set -euo pipefail

# aantal pogingen en interval kun je naar wens tunen
MAX_RETRIES=30
SLEEP_SECONDS=2

for i in $(seq 1 $MAX_RETRIES); do
  code=$(curl -s -o /dev/null \
         --resolve doc-gen.eu:80:127.0.0.1 \
         -w '%{http_code}' \
         http://doc-gen.eu/health/ || true)
  echo "Health check attempt $i: HTTP $code"
  if [ "$code" -eq 200 ]; then
    echo "→ OK"
    exit 0
  fi
  sleep $SLEEP_SECONDS
done

echo "→ FAIL: geen 200 na $MAX_RETRIES pogingen"
exit 1
