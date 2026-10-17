#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"
work=$(mktemp -d)
export COMPOSE_PROJECT_NAME="kex-lab-observability-$(basename "$work" | tr '[:upper:].' '[:lower:]-')"
export BIND_ADDR=127.0.0.1 KAFKA_PORT=0 EXPLORER_PORT=0 KEX_AGENT_PORT=0 AUTOTUNE_PORT=0 PROMETHEUS_PORT=0 GRAFANA_PORT=0
export KEX_LAB_MESSAGES=0 KEX_LAB_INJECT_INVALID=false
export GRAFANA_ADMIN_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
COMPOSE="docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml -f compose.observability.yml"
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
sh scripts/observability.sh up
KEX_LAB_EXPLORER_URL="http://$($COMPOSE port explorer 8080)"
KEX_LAB_AGENT_URL="http://$($COMPOSE port agent 8081)"
KEX_LAB_AUTOTUNE_URL="http://$($COMPOSE port autotune 8080)"
KEX_LAB_PROMETHEUS_URL="http://$($COMPOSE port prometheus 9090)"
KEX_LAB_GRAFANA_URL="http://$($COMPOSE port grafana 3000)"
export KEX_LAB_EXPLORER_URL KEX_LAB_AGENT_URL KEX_LAB_AUTOTUNE_URL KEX_LAB_PROMETHEUS_URL KEX_LAB_GRAFANA_URL
KEX_LAB_HEALTH_PROFILE=observability sh scripts/wait-ready.sh
KEX_LAB_MESSAGES=25 sh scripts/scenario-assert.sh basic
KEX_LAB_MESSAGES=3 sh scripts/scenario-assert.sh dlt
python3 scripts/check-observability.py
sh scripts/report.sh observability
echo 'Observability smoke passed; report and metrics evidence are under reports/.'
