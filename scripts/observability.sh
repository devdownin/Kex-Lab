#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"
COMPOSE="docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml -f compose.observability.yml"
case "${1:-up}" in
  up) $COMPOSE up -d kafka explorer agent autotune lab-metrics prometheus grafana ;;
  down) $COMPOSE down ;;
  *) echo "Usage: $0 {up|down}" >&2; exit 2 ;;
esac
