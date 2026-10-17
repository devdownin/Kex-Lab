# Evaluation guide

The goal is to get useful evidence quickly, then deepen only the component you need.

## 15 minutes — core integration

1. Copy configuration: `cp .env.example .env`.
2. Replace the two development tokens in `.env`.
3. Run `make up`.
4. Run `make wait`, then `make smoke`.
5. Open Explorer on http://localhost:8080 and Kex-anHarness on http://localhost:8081.
6. In Explorer, verify the broker is reachable and inspect topics.
7. If an LLM key is configured, ask Kex-anHarness to list Kafka topics. The useful evidence is not only the answer: verify that the conversation reports an MCP tool call.

Success criteria:

- Kafka responds.
- Explorer liveness is UP.
- Agent health is UP.
- Explorer can inspect the shared broker.
- With a model configured, the agent discovers and calls Explorer through MCP.

## Optional Kafka operational review

See [the operational review walkthrough](OPERATIONAL-REVIEWS.md) for the
compatible image prerequisite and `make profile-reviews`. Check the `lab`
topic policy, take two complete readings of an actual consumer group's lag,
then review the demo DLT. Record `NOT_CONFIGURED` or `UNMEASURED` as a lack of
evidence, not as a pass. A DLT source route is an operator declaration; a
malformed source record does not demonstrate that it was forwarded.

## 30–60 minutes — Kafka SQL Explorer

```bash
make components
sh scripts/evaluate.sh explorer
```

Use the upstream seeded sandbox to evaluate topic browsing, SQL, schema inference, stream tracing, data model and cluster audit. This scenario is richer than the minimal Lab broker and remains maintained by the Explorer project.

## 30–60 minutes — KafkaConsumerAutoTune

```bash
make components
sh scripts/evaluate.sh autotune
```

The upstream stack starts Kafka, Oracle XE and its observability services. Evaluate:

- live throughput and lag;
- PID optimizer interventions;
- per-partition consumer state;
- circuit-breaker behavior;
- DLT isolation and replay;
- Jaeger traces and Prometheus/Grafana metrics.

This stack uses its own ports and Kafka. Stop the core Lab first with `make down` to avoid collisions.

## SpectraLLM

```bash
make components
sh scripts/evaluate.sh spectra
```

The script delegates to Spectra's maintained `start.sh --first-run --hub` path. The first run downloads model weights and is intentionally not part of the five-minute core path.

Evaluate document ingestion, cited RAG answers, retrieval inspection and — if your hardware/resources allow it — the fine-tuning workflow.

## Reset

Core Lab:

```bash
make reset
```

Individual upstream scenarios should be stopped from their own checkout under `.components/`, using their documented shutdown command. Kex Lab never deletes those repositories automatically.

## What Kex Lab should eventually prove end-to-end

The target demonstration is an observable business flow in Kafka where:

1. traffic is produced;
2. AutoTune consumes it and adapts under changing load;
3. Explorer exposes the actual Kafka state and traces;
4. Kex-anHarness diagnoses the situation using Explorer MCP evidence;
5. optional SpectraLLM supplies private domain knowledge/local inference;
6. every automated conclusion can be traced back to observations.

That scenario should be added incrementally using stable APIs rather than coupling the four codebases.

## Repository checks

Run `make check` for the shell-entry-point and TimesFM HTTP contracts, strict
Kafka offset checks, immutable image-pin consistency, shell syntax, source
links and all six Compose profiles. It starts no containers and validates using
`.env.example` rather than the local `.env`. Docker Engine is required for the
separate runtime checks, not for `docker compose config`.

Use `make health PROFILE=core` for Kafka/Explorer, `PROFILE=ai` for the Agent,
`PROFILE=reviews` for operational reviews, `PROFILE=demo` for AutoTune,
`PROFILE=full` for Spectra, and `PROFILE=observability` for Prometheus/Grafana.
The same selector works with `make smoke` and `make wait`. A missing or unhealthy
expected service fails the command; optional services outside the chosen profile
are not probed. HTTP health does not establish successful model inference.

`make integration-smoke` starts real core and AutoTune services in a unique
Compose project with ephemeral loopback ports. It verifies exact offset increases
for basic and DLT traffic and checks the poison record only in newly appended
ranges. It prints logs on failure and removes only its own resources on exit.
A normal Lab can remain running alongside this test.

## Guided demo and report

Use `make demo-lite` for Kafka, Explorer, AutoTune and the Agent without Spectra
or a model download. It asserts the basic injection, waits for readiness and
writes a report. Start with a Docker allocation of 4 CPUs, 8 GB RAM and 10 GB
free disk; this is a planning budget, not a performance measurement.

`make report PROFILE=demo` captures actual container image IDs/registry digests,
current health and interface links. Assertions are recorded independently by
`make scenario-assert` as timestamped JSON under `reports/assertions/`. A report
selects the latest assertion per scenario for its project and topic and preserves
its source commit and dirty-worktree flag. No matching records is `UNMEASURED`,
not proof of a passing scenario. Markdown and JSON are written even on failure.

Use `make observability-smoke` for an isolated real Grafana/Prometheus test,
including authenticated Agent scraping and the measured lag adapter. It removes
only its own containers/volumes and leaves its report under `reports/`.
See [observability details](OBSERVABILITY.md) and [release preparation](RELEASING.md).
