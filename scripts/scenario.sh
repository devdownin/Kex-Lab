#!/usr/bin/env sh
set -eu
SCENARIO="${1:-basic}"
case "$SCENARIO" in
 basic) export KEX_LAB_MESSAGES="${KEX_LAB_MESSAGES:-500}" ;;
 lag) export KEX_LAB_MESSAGES="${KEX_LAB_MESSAGES:-10000}" ;;
 overload) export KEX_LAB_MESSAGES="${KEX_LAB_MESSAGES:-50000}" ;;
 dlt) export KEX_LAB_MESSAGES="${KEX_LAB_MESSAGES:-500}"; export KEX_LAB_INJECT_INVALID=true ;;
 *) echo "Usage: $0 {basic|lag|dlt|overload}" >&2; exit 2 ;;
esac
. "$(dirname -- "$0")/common.sh"
echo "Scenario: $SCENARIO ($KEX_LAB_MESSAGES records)"
sh scripts/demo.sh
