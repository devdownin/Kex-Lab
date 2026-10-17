#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"
docker compose --env-file versions.env -f compose.yml ps
printf '\nEndpoints\n'
printf '  Explorer : http://localhost:%s\n' "${EXPLORER_PORT:-8080}"
printf '  Kex-anHarness: http://localhost:%s\n' "${KEX_AGENT_PORT:-8081}"
