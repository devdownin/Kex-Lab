#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && set -a && . ./.env && set +a

check() {
  name="$1"; url="$2"; version="$3"
  if command -v curl >/dev/null 2>&1 && curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then state="UP"; else state="CHECK"; fi
  printf "%-12s %-8s %-28s %s\n" "$name" "$state" "$version" "$url"
}

echo "Kex Lab health"
printf "%-12s %-8s %-28s %s\n" "SERVICE" "STATE" "IMAGE" "URL"
printf "%-12s %-8s %-28s %s\n" "-------" "-----" "-----" "---"
check "Explorer" "http://localhost:${EXPLORER_PORT:-8080}" "${EXPLORER_IMAGE:-see versions.env}"
check "Agent" "http://localhost:${KEX_AGENT_PORT:-8081}" "${KEX_AGENT_IMAGE:-see versions.env}"
check "AutoTune" "http://localhost:${AUTOTUNE_PORT:-8082}/dashboard" "${AUTOTUNE_IMAGE:-see versions.env}"
check "Spectra" "http://localhost:${SPECTRA_FRONTEND_PORT:-8084}" "${SPECTRALLM_FRONTEND_IMAGE:-see versions.env}"
echo
echo "Container health:"
sh scripts/hub.sh ps
