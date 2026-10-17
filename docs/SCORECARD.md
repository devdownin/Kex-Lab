# Evaluation scorecard

The scorecard records evidence, not a product ranking.

| Check | Expected evidence |
|---|---|
| Environment | `make doctor` returns no errors |
| Core startup | Kafka, Explorer and Agent containers running |
| Kafka | broker API responds |
| Explorer | liveness endpoint returns success |
| Agent | health endpoint returns success |
| AutoTune | application health UP and workload counters observed |
| Basic scenario | 500 records produced |
| Lag scenario | 10,000 records create observable consumer activity |
| DLT scenario | deliberately invalid record is injected and its handling can be inspected |
| Overload scenario | 50,000 records provide sustained load |
| MCP | Agent trace shows Explorer tool invocation |
| Optional topic review | `lab` policy result cites replica/ISR/configuration evidence or reports `NOT_CONFIGURED` / `UNMEASURED` |
| Optional lag trend | Two complete readings for the same topic/group; the first reading alone has no trend |
| Optional DLT review | Source declaration is separate from observed Kafka metadata; replay/monitoring are not inferred |
| Observability | four targets scrape successfully; provisioned Grafana dashboard and measured AutoTune lag verified |
| Reproducibility | observed container image IDs and registry digests captured alongside the source version |
| Report | `reports/latest.md` and `reports/latest.json` retain health and dated assertion evidence |

Run `make report PROFILE=demo` after an asserted scenario. Reports distinguish current health from historical assertion evidence and retain the source commit/worktree state. Missing measurements stay `UNMEASURED`.
