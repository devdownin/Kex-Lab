#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] || { echo 'Prepare the standard Lab .env first (see README).' >&2; exit 2; }
set -a
. ./.env
set +a
case "${1:-}" in
 prepare)
  command -v git >/dev/null
  command -v python3 >/dev/null
  if [ ! -f .env.timesfm ]; then
    python3 - <<'PY'
from pathlib import Path
import secrets
content = Path('scenarios/timesfm/env.example').read_text()
for _ in range(content.count('GENERATE_SECRET')):
    content = content.replace('GENERATE_SECRET', secrets.token_hex(32), 1)
p = Path('.env.timesfm')
p.touch(mode=0o600, exist_ok=False)
p.write_text(content)
PY
  fi
  set -a
  . ./.env.timesfm
  set +a
  mkdir -p .timesfm/sources
  for repo in Kafkaexplorer Kex-agent-ai; do
    case "$repo" in
      Kafkaexplorer) revision="$KEX_TIMESFM_EXPLORER_REF" ;;
      Kex-agent-ai) revision="$KEX_TIMESFM_AGENT_REF" ;;
    esac
    printf '%s' "$revision" | python3 -c 'import re,sys; assert re.fullmatch("[a-f0-9]{40}", sys.stdin.read()), "Expected an exact commit SHA"'
    target=".timesfm/sources/$repo"
    if [ ! -d "$target" ]; then
      git init -q "$target"
      git -C "$target" remote add origin "https://github.com/devdownin/$repo.git"
      git -C "$target" fetch -q --depth 1 origin "$revision"
      git -C "$target" checkout -q --detach FETCH_HEAD
    fi
    [ "$(git -C "$target" rev-parse HEAD)" = "$revision" ] || { echo "Source revision differs in $target; preserve your work and choose a fresh directory." >&2; exit 2; }
    [ -z "$(git -C "$target" status --porcelain)" ] || { echo "Uncommitted changes in $target; use clean sources for this scenario." >&2; exit 2; }
  done
  if [ ! -f .timesfm/pilot.yml ]; then
    printf '%s\n' '{"explorer":{"forecasting":{"pilot":{"enabled":false}}}}' > .timesfm/pilot.yml
  fi
  echo 'Prepared pinned sources, isolated model/DB credentials and pilot configuration.'
  ;;
 up|reload|status|stop)
  [ -f .env.timesfm ] || { echo 'Run prepare first.' >&2; exit 2; }
  command -v docker >/dev/null
  case "$1" in
   up) docker compose --env-file .env --env-file .env.timesfm -p kex-lab-timesfm -f compose.yml -f compose.timesfm.yml up -d --build --wait --wait-timeout 900 ;;
   reload)
    docker compose --env-file .env --env-file .env.timesfm -p kex-lab-timesfm -f compose.yml -f compose.timesfm.yml up -d --no-deps --force-recreate --wait --wait-timeout 180 explorer
    docker compose --env-file .env --env-file .env.timesfm -p kex-lab-timesfm -f compose.yml -f compose.timesfm.yml up -d --no-deps --force-recreate --wait --wait-timeout 180 agent
    ;;
   status) docker compose --env-file .env --env-file .env.timesfm -p kex-lab-timesfm -f compose.yml -f compose.timesfm.yml ps ;;
   stop) docker compose --env-file .env --env-file .env.timesfm -p kex-lab-timesfm -f compose.yml -f compose.timesfm.yml stop ;;
  esac
  ;;
 *) echo "Usage: $0 {prepare|up|reload|status|stop}" >&2; exit 2 ;;
esac
