#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"
exec python3 scripts/lab_report.py report --profile "${1:-${KEX_LAB_HEALTH_PROFILE:-ai}}"
