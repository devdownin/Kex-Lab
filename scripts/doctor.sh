#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"
command -v python3 >/dev/null 2>&1 || { echo 'ERROR Python 3 required. Install python3, then rerun make doctor.' >&2; exit 1; }
exec python3 scripts/doctor.py "$@"
