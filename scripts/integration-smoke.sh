#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && set -a && . ./.env && set +a

COMPOSE="docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml"
cleanup() { $COMPOSE down -v --remove-orphans >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM

$COMPOSE up -d kafka explorer agent autotune
sh scripts/wait-ready.sh
KEX_LAB_MESSAGES=25 $COMPOSE run --rm traffic

docker compose --env-file versions.env -f compose.yml exec -T kafka   /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic demo.app.topic >/dev/null
curl -fsS "http://127.0.0.1:${EXPLORER_PORT:-8080}/actuator/health/liveness" >/dev/null
curl -fsS "http://127.0.0.1:${KEX_AGENT_PORT:-8081}/actuator/health" >/dev/null

echo "Integrated smoke test passed: Kafka traffic injected; Explorer and Agent healthy."
