#!/usr/bin/env sh
# Backward-compatible scenario entrypoint. Kafka initialization and seeding
# are centralized in scripts/kafka-init.sh and mounted by Compose.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
exec sh "$ROOT/scripts/kafka-init.sh"
