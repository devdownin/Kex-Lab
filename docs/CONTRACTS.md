# Integration contracts

Kex Lab treats integration points as contracts rather than implementation details.

| Client | Server | Contract | Verification |
|---|---|---|---|
| traffic generator | Kafka | `demo.app.topic`, JSON, six partitions | scenario + topic inspection |
| KafkaConsumerAutoTune | Kafka | bootstrap server + `demo.app.topic` | consumer lag |
| Kafka SQL Explorer | Kafka | Kafka protocol, read/inspection access | liveness + inspection |
| Kex Agent AI | Kafka SQL Explorer | HTTP MCP, token, read-only tools | agent tool trace |
| Optional review profile | Kafka SQL Explorer | `lab` topic policy, declared DLT source, persisted lag baseline | tool catalog and two complete lag readings |
| Prometheus | Lab services | `/actuator/prometheus` where exposed | scrape target state |

## Compatibility rules

1. Kafka bootstrap addresses are configuration.
2. The Lab topic is `demo.app.topic`, matching AutoTune's maintained default.
3. Agent-to-Explorer access goes through MCP; the Agent gets no direct Kafka mutation credentials.
4. Health and metrics checks fail visibly when capabilities disappear.
5. Image changes go through `versions.env` or explicit overrides.
6. Breaking changes to these contracts require a Kex-Lab compatibility update.
7. The optional `lab` topic policy models one broker only; missing policy or unread Kafka data cannot be reported as compliant.
