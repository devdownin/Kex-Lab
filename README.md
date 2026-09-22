<div align="center">

# Kex Lab

### AI-assisted Kafka operations — observable, adaptive, local.

**Run and evaluate the complete Kex stack on your machine.**

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kafka](https://img.shields.io/badge/Apache-Kafka-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![MCP](https://img.shields.io/badge/MCP-read--only-5C5C5C)](https://modelcontextprotocol.io/)
[![GitHub](https://img.shields.io/badge/source-open-181717?logo=github)](https://github.com/devdownin/Kex-Lab)

**Observe Kafka · Adapt consumers · Diagnose with AI · Keep knowledge local**

</div>

---

Kex Lab connects four open-source projects around one Kafka broker so developers and platform teams can evaluate Kafka inspection, adaptive consumption, AI-assisted diagnosis and optional local AI capabilities in one reproducible environment.

```mermaid
flowchart LR
  P[Produce Kafka traffic] --> K[(Kafka)]
  K --> T[KafkaConsumerAutoTune]
  K --> E[Kafka SQL Explorer]
  E -->|read-only MCP| A[Kex Agent AI]
  S[SpectraLLM] -. optional local AI / knowledge .-> A
```

### One lab, four complementary capabilities

| Observe | Adapt | Diagnose | Knowledge |
|:---:|:---:|:---:|:---:|
| **Kafka SQL Explorer** | **KafkaConsumerAutoTune** | **Kex Agent AI** | **SpectraLLM** |
| Inspect, query, trace and audit Kafka | Adapt consumer settings to Kafka traffic | Use read-only Kafka evidence through MCP | Add optional private local AI and RAG |

The integrated demo produces Kafka traffic, lets **KafkaConsumerAutoTune** consume and adapt, exposes the broker through **Kafka SQL Explorer**, and gives **Kex Agent AI** a read-only MCP path for assisted diagnosis. **SpectraLLM** adds optional local AI and knowledge capabilities.

Kex Lab is an integration and evaluation repository. The four products remain independent projects.

## 🚀 Start here

Requirements: Docker Engine with Compose v2.

### Evaluate the complete published stack

No application source build is required. Kex Lab uses the published Docker Hub images for the four projects (five application images because SpectraLLM has separate backend and frontend images).

```bash
cp .env.example .env
make doctor
make hub-up
make hub-status
```

Open:

- Kafka SQL Explorer: **http://localhost:8080**
- Kex Agent AI: **http://localhost:8081**
- KafkaConsumerAutoTune: **http://localhost:8082/dashboard**
- SpectraLLM: **http://localhost:8084**

SpectraLLM still needs its model artifacts. With `SPECTRA_STARTUP_AUTO_INSTALL_MODELS=true`, its API may download the default models on first startup. Kex Agent chat requires a configured model provider/API key.

Stop the complete stack with `make hub-down`.

### Run the Kafka diagnosis scenario

```bash
make demo-basic
```

Additional reproducible scenarios:

```bash
make demo-lag
make demo-dlt
make demo-overload
make report
```

### Evaluate only the core

For Kafka + Explorer + Kex Agent:

```bash
cp .env.example .env
make doctor
make up
make status
make smoke
```

Stop with `make down`, or use `make reset` to also remove volumes.

## 🧩 Components

| Project | What it contributes to the Lab |
|---|---|
| [Kex Agent AI](https://github.com/devdownin/Kex-agent-ai) | Uses governed actions, supervision and human approval; accesses Kafka evidence through Explorer's MCP tools |
| [Kafka SQL Explorer](https://github.com/devdownin/Kafkaexplorer) | Inspects, queries, traces and audits Kafka; exposes read-only MCP tools |
| [KafkaConsumerAutoTune](https://github.com/devdownin/kafkaconsumerautotune) | Consumes Kafka traffic and adapts consumer settings using PID-based tuning, with resilience and observability |
| [SpectraLLM](https://github.com/devdownin/SpectraLLM) | Provides optional private local RAG, document ingestion, fine-tuning and local LLM serving |

## 🏗️ Architecture

```mermaid
flowchart LR
  K[(Kafka 4.3)] --> E[Kafka SQL Explorer]
  K --> T[KafkaConsumerAutoTune]
  E -->|MCP / read-only tools| A[Kex Agent AI]
  S[SpectraLLM] -. private LLM / knowledge .-> E
  S -. local AI .-> A
  T -. consumer state / metrics .-> K
```

## 📊 Evaluation and observability

Individual products can also be evaluated from their upstream repositories. `make components` clones them under `.components/`; then run `sh scripts/evaluate.sh <component>`.

For the integrated Lab, optional cross-project observability is available with:

```bash
make observability-up
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000
```

Image versions are centralized in `versions.env`. See [docs/EVALUATION.md](docs/EVALUATION.md) for evaluation paths, [docs/END-TO-END.md](docs/END-TO-END.md) for the traffic-to-diagnosis demo, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for architecture, [docs/CONTRACTS.md](docs/CONTRACTS.md) for integration boundaries and [docs/SCORECARD.md](docs/SCORECARD.md) for the evidence checklist.

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
│   ├── status.sh
│   ├── smoke-test.sh
│   └── evaluate.sh
└── docs/
    ├── ARCHITECTURE.md
    └── EVALUATION.md
```

## 📄 Licenses

Each upstream project keeps its own license. Consult the corresponding repository before redistribution or modification.
