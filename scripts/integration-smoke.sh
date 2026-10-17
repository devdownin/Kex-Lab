#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"

# Never reuse the normal Lab project, its volumes or its published ports.
work=$(mktemp -d)
export COMPOSE_PROJECT_NAME="kex-lab-test-$(basename "$work" | tr '[:upper:].' '[:lower:]-')"
export BIND_ADDR=127.0.0.1 KAFKA_PORT=0 EXPLORER_PORT=0 KEX_AGENT_PORT=0 AUTOTUNE_PORT=0
export KEX_LAB_MESSAGES=0 KEX_LAB_INJECT_INVALID=false
COMPOSE="docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml"
cleanup() {
  status=$?
  trap - EXIT
  if [ "$status" -ne 0 ]; then $COMPOSE logs --no-color >&2 || true; fi
  $COMPOSE down -v --remove-orphans || status=1
  rm -rf "$work"
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "Isolated integration project: $COMPOSE_PROJECT_NAME"
# Exercise the public guided path, with one explicitly measured injection.
KEX_LAB_MESSAGES=25 sh scripts/demo-lite.sh
# The subsequent DLT check and report keep the isolated project's URLs.
KEX_LAB_EXPLORER_URL="http://$($COMPOSE port explorer 8080)"
KEX_LAB_AGENT_URL="http://$($COMPOSE port agent 8081)"
KEX_LAB_AUTOTUNE_URL="http://$($COMPOSE port autotune 8080)"
export KEX_LAB_EXPLORER_URL KEX_LAB_AGENT_URL KEX_LAB_AUTOTUNE_URL
KEX_LAB_MESSAGES=3 sh scripts/scenario-assert.sh dlt

sh scripts/report.sh demo

echo "Integrated smoke passed: isolated stack healthy; exact basic and DLT offset increases verified."
