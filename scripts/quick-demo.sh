#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

sh scripts/doctor.sh
sh scripts/hub.sh up

echo "Waiting for the Kex Lab services..."
sh scripts/wait-ready.sh || true

echo "Injecting the reproducible basic Kafka scenario..."
sh scripts/scenario.sh basic

echo
sh scripts/health.sh
echo
echo "Kex Lab demo is ready:"
echo "  Explorer : http://localhost:${EXPLORER_PORT:-8080}"
echo "  Agent    : http://localhost:${KEX_AGENT_PORT:-8081}"
echo "  AutoTune : http://localhost:${AUTOTUNE_PORT:-8082}/dashboard"
echo "  Spectra  : http://localhost:${SPECTRA_FRONTEND_PORT:-8084}"
echo
echo "Next: inspect the generated topic in Explorer, observe the consumer in AutoTune,"
echo "then use the Agent to investigate the Kafka evidence exposed through MCP."
