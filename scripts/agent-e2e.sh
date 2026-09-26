#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && set -a && . ./.env && set +a

: "${KEX_AGENT_API_KEY:?KEX_AGENT_API_KEY is required}"
AGENT_URL="${KEX_AGENT_URL:-http://127.0.0.1:${KEX_AGENT_PORT:-8081}}"
TOPIC="${KEX_LAB_TOPIC:-demo.app.topic}"
PROMPT="Inspect $TOPIC through the Kafka Explorer MCP tools. Report the topic name and cite the Kafka evidence you used."

sh scripts/scenario-assert.sh basic

command -v python3 >/dev/null 2>&1 || { echo 'python3 is required to verify structured Agent tool calls.' >&2; exit 2; }
echo "Calling the Agent chat endpoint..."
response="$(curl -fsS --max-time 150 -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $KEX_AGENT_API_KEY" \
  -d "{\"message\":\"$PROMPT\"}" "$AGENT_URL/api/agent/chat")" || {
    echo 'Agent chat request failed; check the model provider and the MCP connection.' >&2
    exit 2
  }
printf '%s\n' "$response" | python3 -c '
import json, os, sys
try:
    answer = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit("ASSERT FAILED: Agent response is not JSON.")
topic = os.environ.get("KEX_LAB_TOPIC", "demo.app.topic")
if topic not in answer.get("content", ""):
    sys.exit(f"ASSERT FAILED: Agent response did not cite {topic}.")
tools = answer.get("tools") or []
if not any(call.get("tool", "").startswith("kex_") and not call.get("failed", False) for call in tools):
    sys.exit("ASSERT FAILED: Agent returned no successful Explorer MCP tool call.")
print(f"ASSERT PASS: Agent cited {topic} and executed an Explorer MCP tool.")
'
