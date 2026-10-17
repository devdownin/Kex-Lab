#!/usr/bin/env sh
set -eu
exec sh "$(dirname -- "$0")/health.sh" "${1:-${KEX_LAB_HEALTH_PROFILE:-ai}}"
