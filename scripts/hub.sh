#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && set -a && . ./.env && set +a
COMPOSE="docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml -f compose.hub.yml"
case "${1:-up}" in
 pull) $COMPOSE pull ;;
 up)
   $COMPOSE pull
   $COMPOSE up -d kafka explorer agent autotune spectra-chromadb spectra-api spectra-frontend
   echo "Docker Hub profile started"
   echo "Explorer : http://localhost:${EXPLORER_PORT:-8080}"
   echo "Agent    : http://localhost:${KEX_AGENT_PORT:-8081}"
   echo "AutoTune : http://localhost:${AUTOTUNE_PORT:-8082}/dashboard"
   echo "Spectra  : http://localhost:${SPECTRA_FRONTEND_PORT:-8084}"
   ;;
 down) $COMPOSE down ;;
 ps) $COMPOSE ps ;;
 *) echo "Usage: $0 {pull|up|down|ps}" >&2; exit 2 ;;
esac
