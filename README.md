<div align="center">

# Kex Lab

### AI-assisted Kafka operations — observable, adaptive, local.

**Run and evaluate the complete Kex stack on your machine.**

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kafka](https://img.shields.io/badge/Apache-Kafka-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![MCP](https://img.shields.io/badge/MCP-read--only-5C5C5C)](https://modelcontextprotocol.io/)
[![GitHub](https://img.shields.io/badge/source-open-181717?logo=github)](https://github.com/devdownin/Kex-Lab)

**OBSERVE** Kafka · **ADAPT** consumers · **DIAGNOSE** with AI · **KEEP KNOWLEDGE LOCAL**

</div>

---

<table>
<tr>
<td width="25%" align="center"><strong>🔎 OBSERVE</strong><br><sub>Kafka SQL Explorer</sub><br><br>Inspect, query, trace and audit Kafka</td>
<td width="25%" align="center"><strong>⚙️ ADAPT</strong><br><sub>KafkaConsumerAutoTune</sub><br><br>Adapt consumer settings to Kafka traffic</td>
<td width="25%" align="center"><strong>🤖 DIAGNOSE</strong><br><sub>Kex Agent AI</sub><br><br>Use read-only Kafka evidence through MCP</td>
<td width="25%" align="center"><strong>🧠 KNOWLEDGE</strong><br><sub>SpectraLLM</sub><br><br>Optional private local AI and RAG</td>
</tr>
</table>

Kex Lab connects four open-source projects around one Kafka broker so developers and platform teams can evaluate Kafka inspection, adaptive consumption, AI-assisted diagnosis and optional local AI capabilities in one reproducible environment.

```mermaid
flowchart LR
  P[Produce Kafka traffic] --> K[(Kafka)]
  K --> T[KafkaConsumerAutoTune]
  K --> E[Kafka SQL Explorer]
  E -->|read-only MCP| A[Kex Agent AI]
  S[SpectraLLM] -. optional local AI / knowledge .-> A
```

### From events to insights

The integrated demo produces Kafka traffic, lets **KafkaConsumerAutoTune** consume and adapt, exposes the broker through **Kafka SQL Explorer**, and gives **Kex Agent AI** a read-only MCP path for assisted diagnosis. **SpectraLLM** adds optional local AI and knowledge capabilities.

Kex Lab is an integration and evaluation repository. The four products remain independent projects.

## 🚀 Start here

> **Goal:** get the published Kex applications running together around a shared Kafka broker.

**Requirement:** Docker Engine with Compose v2.

### Complete stack · Docker images

No application source build is required. Kex Lab uses the published Docker Hub images for the four projects (five application images because SpectraLLM has separate backend and frontend images).

```bash
cp .env.example .env
make demo
```

Open:

- Kafka SQL Explorer: **http://localhost:8080**
- Kex Agent AI: **http://localhost:8081**
- KafkaConsumerAutoTune: **http://localhost:8082/dashboard**
- SpectraLLM: **http://localhost:8084**

SpectraLLM still needs its model artifacts. With `SPECTRA_STARTUP_AUTO_INSTALL_MODELS=true`, its API may download the default models on first startup. Kex Agent chat requires a configured model provider/API key.

Kafka initialization is part of the Compose lifecycle: the one-shot `kafka-init` service waits for Kafka, creates the configured application and DLT topics, then seeds the application topic before dependent services start. `make demo` checks prerequisites, starts the published stack, waits for readiness, runs the basic scenario, prints the health dashboard and the application URLs. Stop the complete stack with `make hub-down`.

### 🌱 Kafka initialization

The Compose stack automatically runs `scripts/kafka-init.sh`. Topic creation is idempotent (`--if-not-exists`); seed records are produced each time the initializer runs.

| Setting | Default | Purpose |
|---|---|---|
| `KEX_LAB_TOPIC` | `demo.app.topic` | Application topic |
| `KEX_LAB_DLT_TOPIC` | `demo.app.topic.dlt` | Dead-letter topic |
| `KEX_LAB_PARTITIONS` | `6` | Partitions created for both topics |
| `KEX_LAB_MESSAGES` | `500` | Seed records written to the application topic |
| `KEX_LAB_INJECT_INVALID` | `false` | Optionally adds the poison record used by the DLT scenario |

Explorer, AutoTune and Spectra wait for successful initialization where their Compose profile requires Kafka data. The existing `traffic` service reuses the same initializer, so topic creation and sample generation have one implementation.

### ⚡ Reproduce operational scenarios

```bash
make demo-basic
```

The one-command demo runs the basic scenario. To deliberately create more visible operating conditions:

```bash
make demo-lag
make demo-dlt
make demo-overload
make report
```

Scenario guides are kept under `scenarios/`: `basic`, `consumer-lag`, `invalid-records` and `overload`. Each guide describes what the scenario injects and what to inspect. Run `SCENARIO=lag make scenario-assert` to execute a scenario with machine-checkable assertions. `make agent-e2e` additionally exercises the Agent → Explorer MCP diagnosis when a model provider and a stable Agent chat endpoint are configured.

```bash
make report
```

### 🧭 Choose a deployment profile

| Goal | Command | Components |
|---|---|---|
| Inspect Kafka | `make profile-core` | Kafka + Explorer |
| Add governed AI diagnosis | `make profile-ai` | Kafka + Explorer + Agent |
| Run the complete published stack | `make profile-full` | Kafka + Explorer + Agent + AutoTune + Spectra |
| Run the guided scenario | `make profile-demo` | Full stack + readiness + traffic + health view |

The compatible image set is centralized in `versions.env`, which acts as the Lab compatibility manifest.

### 📦 Prefer a smaller starting point?

For Kafka + Explorer + Kex Agent:

```bash
cp .env.example .env
make doctor
make up
make status
make smoke
```

Stop with `make down`, or use `make reset` to also remove volumes.

## 🧩 Explore the stack

| Project | What it contributes to the Lab |
|---|---|
| [Kex Agent AI](https://github.com/devdownin/Kex-agent-ai) | Uses governed actions, supervision and human approval; accesses Kafka evidence through Explorer's MCP tools |
| [Kafka SQL Explorer](https://github.com/devdownin/Kafkaexplorer) | Inspects, queries, traces and audits Kafka; exposes read-only MCP tools |
| [KafkaConsumerAutoTune](https://github.com/devdownin/kafkaconsumerautotune) | Consumes Kafka traffic and adapts consumer settings using PID-based tuning, with resilience and observability |
| [SpectraLLM](https://github.com/devdownin/SpectraLLM) | Provides optional private local RAG, document ingestion, fine-tuning and local LLM serving |

## 🏗️ How it connects

```mermaid
flowchart LR
  K[(Kafka 4.3)] --> I[kafka-init]\n  I -->|create topics + seed records| K
  K -->|topics / records| E[Kafka SQL Explorer]
  K -->|consumer workload| T[KafkaConsumerAutoTune]
  E -->|read-only MCP tools| A[Kex Agent AI]
  A -->|optional local inference| S[SpectraLLM]
  S -->|optional Kafka ingestion| K
  T -. consumer state / metrics .-> K
```

**Runtime boundaries:** Kafka is the shared event backbone; Explorer owns inspection and the read-only MCP evidence boundary; AutoTune consumes Kafka traffic and adapts its consumer settings; Kex Agent reasons over governed MCP evidence rather than receiving Kafka mutation rights; Spectra is optional local inference/knowledge infrastructure. See [the detailed architecture](docs/ARCHITECTURE.md).

## 📊 Evaluate with evidence

Individual products can also be evaluated from their upstream repositories. `make components` clones them under `.components/`; then run `sh scripts/evaluate.sh <component>`.

For the integrated Lab, optional cross-project observability is available with:

```bash
make health
# Service state, image/version and URL

make observability-up
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000
# Dashboard:  Kex Lab / Kex Lab — Integrated Operations
```

Image versions are centralized in `versions.env`. See [docs/EVALUATION.md](docs/EVALUATION.md) for evaluation paths, [docs/END-TO-END.md](docs/END-TO-END.md) for the traffic-to-diagnosis demo, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for architecture, [docs/CONTRACTS.md](docs/CONTRACTS.md) for integration boundaries and [docs/SCORECARD.md](docs/SCORECARD.md) for the evidence checklist.

## 🏷️ Releases

Kex Lab versions the **integration bundle**, independently from the component release cycles. A tag such as `v1.0.0` identifies a tested Lab configuration; `versions.env` records the component image references included in that bundle.

Pushing a semantic `vX.Y.Z` tag triggers the release workflow, validates the manifest and creates GitHub release notes containing the exact image set. Lab-level changes are tracked in [CHANGELOG.md](CHANGELOG.md).

## 🔒 Principles

- Published images first for fast evaluation.
- One shared Kafka in the core Lab stack.
- Upstream ownership of product-specific infrastructure.
- Loopback binding by default.
- Smoke checks report failures instead of masking unavailable capabilities.
- The Lab is resettable without touching source repositories.

## 📁 Repository layout

```text
.
├── compose.yml
├── .env.example
├── Makefile
├── scripts/
│   ├── components.sh
│   ├── kafka-init.sh\n│   ├── quick-demo.sh
│   ├── health.sh
│   ├── status.sh
│   ├── smoke-test.sh
│   └── evaluate.sh
└── docs/
    ├── ARCHITECTURE.md
    └── EVALUATION.md
```

## 📄 Licenses

Each upstream project keeps its own license. Consult the corresponding repository before redistribution or modification.
