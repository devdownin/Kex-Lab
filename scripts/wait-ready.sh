#!/usr/bin/env sh
set -u
attempts="${1:-30}"
delay="${2:-5}"
i=1
while [ "$i" -le "$attempts" ]; do
  if sh scripts/smoke-test.sh; then
    echo "Kex Lab ready after attempt $i/$attempts"
    exit 0
  fi
  echo "Waiting for Kex Lab ($i/$attempts)..."
  sleep "$delay"
  i=$((i+1))
done
echo "Kex Lab did not become ready" >&2
exit 1
