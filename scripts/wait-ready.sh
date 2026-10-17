#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"
attempts="${1:-30}"
delay="${2:-5}"
case "$attempts" in
  ''|*[!0-9]*|0) echo "Attempts must be a positive integer" >&2; exit 2 ;;
esac
case "$delay" in
  ''|*[!0-9]*) echo "Delay must be a non-negative integer" >&2; exit 2 ;;
esac
i=1
while [ "$i" -le "$attempts" ]; do
  if sh scripts/smoke-test.sh; then
    echo "Kex Lab ready after attempt $i/$attempts"
    exit 0
  fi
  echo "Waiting for Kex Lab ($i/$attempts)..."
  if [ "$i" -lt "$attempts" ]; then sleep "$delay"; fi
  i=$((i+1))
done
echo "Kex Lab did not become ready" >&2
exit 1
