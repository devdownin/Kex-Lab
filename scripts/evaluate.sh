#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TARGET="${1:-all}"

ensure_components() {
  [ -d "$ROOT/.components/Kafkaexplorer" ] || "$ROOT/scripts/components.sh"
}

case "$TARGET" in
  core)
    cd "$ROOT"
    docker compose -f compose.yml up -d
    "$ROOT/scripts/smoke-test.sh"
    ;;
  explorer)
    ensure_components
    cd "$ROOT/.components/Kafkaexplorer"
    docker compose up -d
    echo "Explorer: http://localhost:8080"
    ;;
  autotune)
    ensure_components
    cd "$ROOT/.components/kafkaconsumerautotune"
    docker compose up -d
    echo "AutoTune dashboard: http://localhost:8080/dashboard"
    ;;
  spectra)
    ensure_components
    cd "$ROOT/.components/SpectraLLM"
    ./scripts/start.sh --first-run --hub
    ;;
  agent)
    ensure_components
    echo "Use 'make up' for the pre-wired Agent + Explorer evaluation."
    echo "Upstream checkout: $ROOT/.components/Kex-agent-ai"
    ;;
  all)
    echo "Run the evaluation paths independently to avoid port and infrastructure collisions:"
    echo "  ./scripts/evaluate.sh core"
    echo "  ./scripts/evaluate.sh autotune"
    echo "  ./scripts/evaluate.sh spectra"
    ;;
  *)
    echo "Usage: $0 {core|explorer|agent|autotune|spectra|all}" >&2
    exit 2
    ;;
esac
