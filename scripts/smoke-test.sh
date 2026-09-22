#!/usr/bin/env sh
set -u
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && set -a && . ./.env && set +a

pass=0
fail=0
check() {
  label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '✓ %s\n' "$label"; pass=$((pass + 1))
  else
    printf '✗ %s\n' "$label"; fail=$((fail + 1))
  fi
}

echo "KEX LAB — smoke test"
echo "────────────────────────────────"
check "Docker Compose stack is readable" docker compose -f compose.yml config -q
check "Kafka container is running" docker compose -f compose.yml exec -T kafka /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092
check "Explorer health is UP" curl -fsS "http://127.0.0.1:${EXPLORER_PORT:-8080}/actuator/health/liveness"
check "Kex Agent health is UP" curl -fsS "http://127.0.0.1:${KEX_AGENT_PORT:-8081}/actuator/health"

echo "────────────────────────────────"
printf 'Result: %s passed, %s failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
