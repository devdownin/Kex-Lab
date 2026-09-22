#!/usr/bin/env sh
set -u
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && set -a && . ./.env && set +a
fail=0; warn=0
ok(){ printf '✓ %s\n' "$1"; }
bad(){ printf '✗ %s\n' "$1"; fail=$((fail+1)); }
warning(){ printf '! %s\n' "$1"; warn=$((warn+1)); }
command -v docker >/dev/null 2>&1 && ok "Docker installed" || bad "Docker not found"
docker info >/dev/null 2>&1 && ok "Docker daemon reachable" || bad "Docker daemon unavailable"
docker compose version >/dev/null 2>&1 && ok "Docker Compose v2 available" || bad "Docker Compose v2 unavailable"
command -v curl >/dev/null 2>&1 && ok "curl available" || bad "curl required"
kb="$(df -Pk . 2>/dev/null | awk 'NR==2 {print $4}')"
[ "${kb:-0}" -ge 10485760 ] && ok "At least 10 GB free disk" || warning "Less than 10 GB free"
check_port(){ port="$1"; label="$2"; if command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]$port$"; then warning "$label port $port in use"; else ok "$label port $port appears free"; fi; }
check_port "${KAFKA_PORT:-9092}" Kafka
check_port "${EXPLORER_PORT:-8080}" Explorer
check_port "${KEX_AGENT_PORT:-8081}" Agent
check_port "${AUTOTUNE_PORT:-8082}" AutoTune
[ "${EXPLORER_MCP_AUTH_TOKEN:-change-me-local-mcp-token}" != "change-me-local-mcp-token" ] && ok "MCP token customized" || warning "Default MCP token"
[ "${KEX_AGENT_API_KEY:-change-me-local-agent-key}" != "change-me-local-agent-key" ] && ok "Agent API key customized" || warning "Default Agent key"
echo "Doctor result: $fail error(s), $warn warning(s)"
[ "$fail" -eq 0 ]
