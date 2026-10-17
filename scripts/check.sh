#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
for script in scripts/*.sh scenarios/end-to-end/*.sh; do
  sh -n "$script"
done
python3 scripts/check-repository-links.py
python3 -m unittest discover -s tests -v
python3 scripts/check-compose.py
