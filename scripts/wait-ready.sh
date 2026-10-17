#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"
verbose=false
# Keep the existing positional interface, with --verbose accepted at either end.
if [ "${1:-}" = --verbose ]; then verbose=true; shift; fi
case "${4:-}" in
  --verbose) verbose=true ;;
  '') ;;
  *) echo 'Usage: wait-ready.sh [attempts] [delay] [profile] [--verbose]' >&2; exit 2 ;;
esac
[ "$#" -le 4 ] || { echo 'Too many arguments' >&2; exit 2; }
attempts="${1:-30}"
delay="${2:-5}"
case "$attempts" in
  ''|*[!0-9]*|0) echo "Attempts must be a positive integer" >&2; exit 2 ;;
esac
case "$delay" in
  ''|*[!0-9]*) echo "Delay must be a non-negative integer" >&2; exit 2 ;;
esac
log=$(mktemp)
trap 'rm -f "$log"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
started=$(date +%s)
i=1
while [ "$i" -le "$attempts" ]; do
  echo "Readiness check $i/$attempts ($(($(date +%s) - started))s elapsed)..."
  if sh scripts/smoke-test.sh "${3:-${KEX_LAB_HEALTH_PROFILE:-ai}}" > "$log" 2>&1; then
    if [ "$verbose" = true ]; then cat "$log"; fi
    echo "Kex Lab ready after attempt $i/$attempts ($(($(date +%s) - started))s elapsed)"
    exit 0
  else
    status=$?
    if [ "$verbose" = true ] || [ "$status" -eq 2 ] || [ "$i" -eq "$attempts" ]; then cat "$log"; fi
    [ "$status" -ne 2 ] || exit 2
  fi
  echo "Waiting for Kex Lab ($i/$attempts)..."
  if [ "$i" -lt "$attempts" ]; then sleep "$delay"; fi
  i=$((i+1))
done
echo "Kex Lab did not become ready ($(($(date +%s) - started))s elapsed)" >&2
echo "Next: make health PROFILE=${3:-${KEX_LAB_HEALTH_PROFILE:-ai}}; make logs; retry make wait PROFILE=${3:-${KEX_LAB_HEALTH_PROFILE:-ai}} ARGS=--verbose" >&2
exit 1
