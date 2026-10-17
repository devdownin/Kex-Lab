#!/usr/bin/env sh
set -eu
. "$(dirname -- "$0")/common.sh"
sh scripts/doctor.sh
sh scripts/scenario-assert.sh basic
KEX_LAB_HEALTH_PROFILE=demo sh scripts/wait-ready.sh
sh scripts/report.sh demo
echo 'Lightweight demo ready: Kafka → AutoTune → Explorer → Agent.'
echo 'Evidence and interface links: reports/latest.md'
echo 'Stop with make demo-lite-down (keeps Kafka data).'
