# Integrated observability

Run `make observability-up`, then open
[the dashboard](http://localhost:3000/d/kex-lab-operations) in the **Kex Lab**
folder. Grafana uses `admin` and the local `GRAFANA_ADMIN_PASSWORD`; configure
that setting in `.env`. Prometheus is available on `http://localhost:9090`.
The two host ports can be changed with `GRAFANA_PORT` and `PROMETHEUS_PORT`.
Stop this profile with `make observability-down`.

## Evidence shown

| Panel | Source and limit |
|---|---|
| Metrics endpoint availability | Prometheus `up` for Explorer, Agent and AutoTune; scrape success is distinct from application readiness |
| AutoTune consumer lag | `kex_lab_autotune_consumer_lag` from AutoTune's `components.kafkaLag.details.lag`; covers its consumers, not all Kafka groups |
| Lag probe success | `0` means the adapter cannot measure lag; missing lag is never replaced with zero |
| Traffic and errors/retries | AutoTune application counters; error/retry series can be absent until the first such event |
| Batch duration | Time per newly observed batch; undefined when there are no batches |
| JVM heap | Application JVM meters, grouped by scrape job |
| AutoTune application health | Its health endpoint's overall `UP` status, distinct from scrape success |

Rates require at least two scrapes (10 seconds apart) and new traffic. A quiet
Lab can legitimately show zero throughput. Generate more traffic with
`KEX_LAB_MESSAGES=5000 make traffic`. Missing counters remain **No data** rather
than fabricated zero errors. Use `make health PROFILE=observability` for current
container, broker and HTTP health.

## Authentication and adapter

The Agent's Prometheus endpoint requires its configured API key. Compose passes
`KEX_AGENT_API_KEY` to Prometheus as a runtime secret file; the scrape config
references that file instead of embedding the token in the repository. Start
through `make observability-up` so settings are exported consistently.

`lab-metrics` runs the pinned Python image with a read-only filesystem and a
standard-library HTTP adapter. It queries only the internal AutoTune health URL,
including HTTP 503 bodies so critical measured lag remains visible. Invalid or
missing lag exposes a failed probe without a synthetic lag value. The adapter
has no host-published port and does not mount the Docker socket.

## Validation

`make observability-smoke` creates a unique project with ephemeral loopback
ports, starts the seven-service observability stack, asserts basic/DLT traffic,
checks the Grafana dashboard API and all four Prometheus targets, verifies a
measured lag and received-traffic counter, and writes a runtime report. Cleanup
removes only that test project. CI uploads its reports as `observability-evidence`.

Dashboard source: `observability/grafana/dashboards/kex-lab-operations.json`.
The datasource UID is fixed to `kex-lab-prometheus` and the dashboard UID to
`kex-lab-operations`, keeping links and queries stable.
