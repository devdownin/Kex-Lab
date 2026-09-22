#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
SCENARIO="${1:-basic}"
sh scripts/scenario.sh "$SCENARIO"

COMPOSE="docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml"
TOPIC="${KEX_LAB_TOPIC:-demo.app.topic}"

count="$($COMPOSE exec -T kafka /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic "$TOPIC" 2>/dev/null | awk -F: '{sum += $3} END {print sum+0}')"
case "$SCENARIO" in
  basic) min=500 ;;
  lag) min=10000 ;;
  overload) min=50000 ;;
  dlt) min=501 ;;
  *) echo "Unsupported scenario: $SCENARIO" >&2; exit 2 ;;
esac
[ "$count" -ge "$min" ] || { echo "ASSERT FAILED: $TOPIC has $count records, expected >= $min" >&2; exit 1; }
echo "ASSERT PASS: $SCENARIO produced $count records in $TOPIC (>= $min)."

if [ "$SCENARIO" = dlt ]; then
  sample="$($COMPOSE exec -T kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic "$TOPIC" --from-beginning --max-messages "$count" --timeout-ms 10000 2>/dev/null || true)"
  printf '%s\n' "$sample" | grep -q 'not-json-poison-message' || { echo "ASSERT FAILED: poison record not found" >&2; exit 1; }
  echo "ASSERT PASS: invalid record is observable in $TOPIC."
fi
