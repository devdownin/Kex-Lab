#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && set -a && . ./.env && set +a

COMPOSE="docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml"

echo "KEX LAB — end-to-end demo"
echo "Starting Kafka, Explorer, Agent and AutoTune..."
$COMPOSE up -d kafka explorer agent autotune
echo "Producing demo traffic..."
$COMPOSE run --rm traffic
echo
echo "Endpoints:"
echo "  Explorer : http://localhost:${EXPLORER_PORT:-8080}"
echo "  Agent    : http://localhost:${KEX_AGENT_PORT:-8081}"
echo "  AutoTune : http://localhost:${AUTOTUNE_PORT:-8082}/dashboard"
echo
echo "Suggested verification:"
echo "  1. AutoTune: observe demo.app.topic consumption and optimizer metrics."
echo "  2. Explorer: inspect demo.app.topic and its consumer lag."
echo "  3. Agent: ask 'Inspect demo.app.topic and tell me whether its consumers are keeping up.'"
echo "     Verify the answer reports Explorer MCP tool usage."
