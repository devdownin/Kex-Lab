#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
docker compose -f compose.yml ps
printf '\nEndpoints\n'
printf '  Explorer : http://localhost:%s\n' "${EXPLORER_PORT:-8080}"
printf '  Kex Agent: http://localhost:%s\n' "${KEX_AGENT_PORT:-8081}"
