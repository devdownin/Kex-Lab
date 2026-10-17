#!/usr/bin/env sh
# Source from Lab entry points; exported caller settings take precedence.
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT" || exit 1
KEX_LAB_CALLER_ENV=$(export -p)
set -a
. ./versions.env
if [ -f .env ]; then
  . ./.env
fi
set +a
eval "$KEX_LAB_CALLER_ENV"
unset KEX_LAB_CALLER_ENV
