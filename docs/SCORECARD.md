# Evaluation scorecard

The scorecard records evidence, not a product ranking.

| Check | Expected evidence |
|---|---|
| Environment | `make doctor` returns no errors |
| Core startup | Kafka, Explorer and Agent containers running |
| Kafka | broker API responds |
| Explorer | liveness endpoint returns success |
| Agent | health endpoint returns success |
| AutoTune | dashboard reachable in integrated scenario |
| Basic scenario | 500 records produced |
| Lag scenario | 10,000 records create observable consumer activity |
| DLT scenario | deliberately invalid record is injected and its handling can be inspected |
| Overload scenario | 50,000 records provide sustained load |
| MCP | Agent trace shows Explorer tool invocation |
| Observability | Prometheus targets expose available application metrics |
| Reproducibility | image set captured from `versions.env` |
| Report | `reports/latest.md` generated |

Run `make report` after a scenario to capture the current image set, container state and smoke-test result.
