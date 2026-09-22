# Evaluation guide

The goal is to get useful evidence quickly, then deepen only the component you need.

## 15 minutes — core integration

1. Copy configuration: `cp .env.example .env`.
2. Replace the two development tokens in `.env`.
3. Run `make up`.
4. Run `make smoke`.
5. Open Explorer on http://localhost:8080 and Kex Agent on http://localhost:8081.
6. In Explorer, verify the broker is reachable and inspect topics.
7. If an LLM key is configured, ask Kex Agent to list Kafka topics. The useful evidence is not only the answer: verify that the conversation reports an MCP tool call.

Success criteria:

- Kafka responds.
- Explorer liveness is UP.
- Agent health is UP.
- Explorer can inspect the shared broker.
- With a model configured, the agent discovers and calls Explorer through MCP.

## 30–60 minutes — Kafka SQL Explorer

```bash
make components
./scripts/evaluate.sh explorer
```

Use the upstream seeded sandbox to evaluate topic browsing, SQL, schema inference, stream tracing, data model and cluster audit. This scenario is richer than the minimal Lab broker and remains maintained by the Explorer project.

## 30–60 minutes — KafkaConsumerAutoTune

```bash
make components
./scripts/evaluate.sh autotune
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
./scripts/evaluate.sh spectra
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
4. Kex Agent diagnoses the situation using Explorer MCP evidence;
5. optional SpectraLLM supplies private domain knowledge/local inference;
6. every automated conclusion can be traced back to observations.

That scenario should be added incrementally using stable APIs rather than coupling the four codebases.
