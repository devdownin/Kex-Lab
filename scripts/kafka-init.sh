#!/usr/bin/env sh
set -eu

BROKER="${KAFKA_BOOTSTRAP_SERVERS:-kafka:29092}"
TOPIC="${KEX_LAB_TOPIC:-demo.app.topic}"
COUNT="${KEX_LAB_MESSAGES:-500}"
PARTITIONS="${KEX_LAB_PARTITIONS:-6}"
DLT_TOPIC="${KEX_LAB_DLT_TOPIC:-$TOPIC.dlt}"

KAFKA_HOME=/opt/kafka
TOPICS="$KAFKA_HOME/bin/kafka-topics.sh"
PRODUCER="$KAFKA_HOME/bin/kafka-console-producer.sh"

echo "Kex Lab Kafka initialization"
echo "Broker: $BROKER"
echo "Topics: $TOPIC, $DLT_TOPIC"

"$TOPICS" --bootstrap-server "$BROKER" --create --if-not-exists --topic "$TOPIC" --partitions "$PARTITIONS" --replication-factor 1
"$TOPICS" --bootstrap-server "$BROKER" --create --if-not-exists --topic "$DLT_TOPIC" --partitions "$PARTITIONS" --replication-factor 1

i=1
while [ "$i" -le "$COUNT" ]; do
  printf '{"idPassage":"KEX-%06d","eventType":"LAB_TRAFFIC","demo":{"systeme":"kex-lab","state":"READY","detail":{"origin":"kafka-init"}}}\n' "$i"
  i=$((i + 1))
done | "$PRODUCER" --bootstrap-server "$BROKER" --topic "$TOPIC"

if [ "${KEX_LAB_INJECT_INVALID:-false}" = "true" ]; then
  printf 'not-json-poison-message\n' | "$PRODUCER" --bootstrap-server "$BROKER" --topic "$TOPIC"
fi

echo "Kafka initialization complete: $COUNT records produced to $TOPIC"
