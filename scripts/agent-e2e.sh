#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && set -a && . ./.env && set +a

: "${KEX_AGENT_API_KEY:?KEX_AGENT_API_KEY is required}"
AGENT_URL="${KEX_AGENT_URL:-http://127.0.0.1:${KEX_AGENT_PORT:-8081}}"
PROMPT='Inspect demo.app.topic through the Kafka Explorer MCP tools. Report the topic name and whether Kafka evidence was used.'

sh scripts/scenario-assert.sh basic

echo "Discovering Agent chat endpoint..."
for path in /api/chat /api/v1/chat /chat; do
  response="$(curl -fsS --max-time 90 -H "Content-Type: application/json" -H "X-API-Key: $KEX_AGENT_API_KEY" -d "{\"message\":\"$PROMPT\"}" "$AGENT_URL$path" 2>/dev/null || true)"
  [ -n "$response" ] || continue
  printf '%s\n' "$response" | grep -q 'demo.app.topic' || { echo "ASSERT FAILED: Agent response did not cite demo.app.topic" >&2; exit 1; }
  printf '%s\n' "$response" | grep -Eqi 'mcp|explorer|tool|kafka' || { echo "ASSERT FAILED: Agent response contains no Kafka/MCP evidence marker" >&2; exit 1; }
  echo "ASSERT PASS: Agent diagnosed demo.app.topic and returned Kafka/MCP evidence."
  exit 0
done

echo "Agent chat endpoint was not available with the known HTTP contracts. Health/integration CI remains authoritative until the Agent exposes a stable chat-test contract." >&2
exit 2
