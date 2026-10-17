#!/usr/bin/env sh
set -eu
SCENARIO="${1:-basic}"
case "$SCENARIO" in
  basic|dlt) export KEX_LAB_MESSAGES="${KEX_LAB_MESSAGES:-500}" ;;
  lag) export KEX_LAB_MESSAGES="${KEX_LAB_MESSAGES:-10000}" ;;
  overload) export KEX_LAB_MESSAGES="${KEX_LAB_MESSAGES:-50000}" ;;
  *) echo "Unsupported scenario: $SCENARIO" >&2; exit 2 ;;
esac
. "$(dirname -- "$0")/common.sh"
command -v python3 >/dev/null 2>&1 || { echo 'python3 is required for offset assertions.' >&2; exit 2; }
case "$KEX_LAB_MESSAGES" in
  ''|*[!0-9]*|0) echo 'KEX_LAB_MESSAGES must be a positive integer.' >&2; exit 2 ;;
esac
COMPOSE="docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml"
TOPIC="${KEX_LAB_TOPIC:-demo.app.topic}"
expected="$KEX_LAB_MESSAGES"
export KEX_LAB_INJECT_INVALID=false
if [ "$SCENARIO" = dlt ]; then
  export KEX_LAB_INJECT_INVALID=true
  expected=$((expected + 1))
fi

# Initialize topics without seeding; only the explicit traffic run is measured.
KEX_LAB_MESSAGES=0 KEX_LAB_INJECT_INVALID=false $COMPOSE up -d kafka explorer agent autotune
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
get_offsets() {
  $COMPOSE exec -T kafka /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
    --broker-list kafka:29092 --topic "$TOPIC"
}
get_offsets > "$work/before"
$COMPOSE run --rm traffic
get_offsets > "$work/after"
python3 scripts/assert-offsets.py --topic "$TOPIC" --expected "$expected" \
  "$work/before" "$work/after" > "$work/ranges"
echo "ASSERT PASS: $SCENARIO produced exactly $expected new records in $TOPIC."

if [ "$SCENARIO" = dlt ]; then
  # Read only this run's appended ranges; historical poison cannot satisfy this check.
  while read -r partition start count; do
    $COMPOSE exec -T kafka /opt/kafka/bin/kafka-console-consumer.sh \
      --bootstrap-server kafka:29092 --topic "$TOPIC" --partition "$partition" \
      --offset "$start" --max-messages "$count" --timeout-ms 10000 >> "$work/sample"
  done < "$work/ranges"
  grep -qx 'not-json-poison-message' "$work/sample" || { echo 'ASSERT FAILED: no new poison record found.' >&2; exit 1; }
  echo "ASSERT PASS: a new invalid source record is observable in $TOPIC."
fi
