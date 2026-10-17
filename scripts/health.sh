#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"
profile="${1:-${KEX_LAB_HEALTH_PROFILE:-ai}}"
COMPOSE="docker compose --env-file versions.env -f compose.yml"
services="kafka explorer"
case "$profile" in
  core) ;;
  ai) services="$services agent" ;;
  reviews) COMPOSE="$COMPOSE -f compose.operational-reviews.yml"; services="$services agent" ;;
  demo|full|observability)
    COMPOSE="$COMPOSE -f compose.autotune.yml"
    services="$services agent autotune"
    case "$profile" in
      full) COMPOSE="$COMPOSE -f compose.hub.yml"; services="$services spectra-chromadb spectra-api spectra-frontend" ;;
      observability) COMPOSE="$COMPOSE -f compose.observability.yml"; services="$services prometheus grafana" ;;
    esac
    ;;
  *) echo "Usage: $0 {core|ai|reviews|demo|full|observability}" >&2; exit 2 ;;
esac

fail=0
check() {
  label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf 'UP    %s\n' "$label"
  else
    printf 'DOWN  %s\n' "$label"
    fail=$((fail + 1))
  fi
}
container_ready() {
  container=$($COMPOSE ps -q "$1") || return 1
  [ -n "$container" ] || return 1
  state=$(docker inspect --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container") || return 1
  case "$state" in 'running '| 'running healthy') return 0 ;; *) return 1 ;; esac
}
http_ready() {
  curl -fsS --max-time 3 "$1" >/dev/null
}
actuator_ready() {
  body=$(curl -fsS --max-time 3 "$1") || return 1
  printf '%s\n' "$body" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"UP"'
}

echo "Kex Lab health — $profile"
check 'Compose configuration' $COMPOSE config -q
for service in $services; do check "$service container" container_ready "$service"; done
check 'Kafka broker' $COMPOSE exec -T kafka /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server kafka:29092
check 'Explorer liveness' actuator_ready "${KEX_LAB_EXPLORER_URL:-http://127.0.0.1:${EXPLORER_PORT:-8080}}/actuator/health/liveness"
case "$profile" in
  core) ;;
  *) check 'Agent health' actuator_ready "${KEX_LAB_AGENT_URL:-http://127.0.0.1:${KEX_AGENT_PORT:-8081}}/actuator/health" ;;
esac
case "$profile" in
  demo|full|observability)
    check 'AutoTune dashboard' http_ready "${KEX_LAB_AUTOTUNE_URL:-http://127.0.0.1:${AUTOTUNE_PORT:-8082}}/dashboard"
    ;;
esac
if [ "$profile" = full ]; then
  check 'Spectra API health' actuator_ready "http://127.0.0.1:${SPECTRA_API_PORT:-8083}/actuator/health"
  check 'Spectra frontend' http_ready "http://127.0.0.1:${SPECTRA_FRONTEND_PORT:-8084}"
fi
if [ "$profile" = observability ]; then
  check 'Prometheus readiness' http_ready "http://127.0.0.1:${PROMETHEUS_PORT:-9090}/-/ready"
  check 'Grafana health' http_ready "http://127.0.0.1:${GRAFANA_PORT:-3000}/api/health"
fi
echo "Result: $fail failed check(s)"
[ "$fail" -eq 0 ]
