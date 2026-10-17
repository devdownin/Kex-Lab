#!/usr/bin/env sh
set -u
. "$(dirname -- "$0")/common.sh"
cd "$ROOT"; mkdir -p reports; OUT="reports/latest.md"
{
 echo "# Kex Lab evaluation report"; echo
 echo "- Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
 echo "- Scenario messages: ${KEX_LAB_MESSAGES:-500}"; echo
 echo "## Image set"; echo '~~~'; cat versions.env; echo '~~~'; echo
 echo "## Runtime"; echo '~~~'; docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml ps 2>&1 || true; echo '~~~'; echo
 echo "## Smoke test"; echo '~~~'; sh scripts/smoke-test.sh 2>&1 || true; echo '~~~'
} > "$OUT"
echo "Report written to $OUT"
