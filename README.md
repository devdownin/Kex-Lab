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
<td width="25%" align="center"><strong>🤖 DIAGNOSE</strong><br><sub>Kex-anHarness</sub><br><br>Use read-only Kafka evidence through MCP</td>
<td width="25%" align="center"><strong>🧠 KNOWLEDGE</strong><br><sub>SpectraLLM</sub><br><br>Optional private local AI and RAG</td>
</tr>
</table>

Kex Lab connects four open-source projects around one Kafka broker so developers and platform teams can evaluate Kafka inspection, adaptive consumption, AI-assisted diagnosis and optional local AI capabilities in one reproducible environment.

![Kex Lab architecture: demo traffic enters Apache Kafka; Explorer inspects Kafka evidence; AutoTune consumes traffic; Kex-anHarness calls Explorer through read-only MCP tools; SpectraLLM provides optional local inference and knowledge.](docs/assets/kex-lab-architecture.png)

Editable companions: [SVG](docs/assets/kex-lab-architecture.svg) ·
[Mermaid source](docs/assets/kex-lab-architecture.mmd).

### From events to insights

The integrated demo produces Kafka traffic, lets **KafkaConsumerAutoTune** consume and adapt, exposes the broker through **Kafka SQL Explorer**, and gives **Kex-anHarness** a read-only MCP path for assisted diagnosis. **SpectraLLM** adds optional local AI and knowledge capabilities.

Kex Lab is an integration and evaluation repository. The four products remain independent projects.

## 🚀 Start here

> **Goal:** get the published Kex applications running together around a shared Kafka broker.

**Requirements:** Docker Engine with Compose v2, Make, a POSIX shell and curl. Python 3 is needed for repository checks, scenario assertions and Agent end-to-end assertions.

### Lightweight guided demo

```bash
make demo-lite
```

This starts Kafka, Explorer, AutoTune and the Agent, waits for the `demo` profile,
verifies one traffic injection and writes `reports/latest.md` plus
`reports/latest.json`. It requires no Spectra model download. A provider key is
needed only for an actual Agent reasoning/tool-call evaluation.

As a starting workstation budget, allocate **4 CPUs, 8 GB RAM and 10 GB free
disk** to Docker; this is a planning recommendation, not a benchmark guarantee.
Image downloads and startup time depend on the host and network. The full
Spectra profile needs additional resources for the selected models.

```bash
make health PROFILE=demo
make report PROFILE=demo
make demo-lite-down   # Stop the lightweight stack and preserve Kafka data
```

### Complete stack · Docker images

No application source build is required. Kex Lab uses the published Docker Hub images for the four projects (five application images because SpectraLLM has separate backend and frontend images).

```bash
cp .env.example .env
make demo
```

Open:

- Kafka SQL Explorer: **http://localhost:8080**
- Kex-anHarness: **http://localhost:8081**
- KafkaConsumerAutoTune: **http://localhost:8082/dashboard**
- SpectraLLM: **http://localhost:8084**

SpectraLLM still needs its model artifacts. With `SPECTRA_STARTUP_AUTO_INSTALL_MODELS=true`, its API may download the default models on first startup. Kex-anHarness chat requires a configured model provider/API key.

Kafka initialization is part of the Compose lifecycle: the one-shot `kafka-init` service waits for Kafka, creates the configured application and DLT topics, then seeds the application topic before dependent services start. `make demo` checks prerequisites, starts the published stack, waits for readiness, runs the basic scenario, prints the health dashboard and the application URLs. Stop the complete stack with `make hub-down`.

### Configuration and checks

Run commands from the repository root. `make setup` creates `.env` if missing;
review it before starting services. `versions.env` supplies image defaults,
`.env` supplies local settings, and exported shell variables override both.
For example, `KEX_LAB_MESSAGES=5000 make traffic` adds 5,000 records to the
configured `KEX_LAB_TOPIC`. The traffic service also uses `KEX_LAB_DLT_TOPIC`
and `KEX_LAB_PARTITIONS` when creating topics.

Scenario defaults are 500 records for `basic` and `dlt`, 10,000 for `lag`,
and 50,000 for `overload`; an exported `KEX_LAB_MESSAGES` overrides these.
The DLT scenario adds one poison record to the source topic. Scenario assertions
initialize topics without seed traffic, capture every partition's offsets, inject
traffic once, and require an exact increase of the requested count (plus one for
DLT). The DLT check reads only newly appended ranges. Concurrent producers,
partition changes or offset rewinds make the assertion fail; automatic DLT
forwarding remains outside this check.

```bash
make setup
make wait        # Requires a running core stack; fails if it never becomes ready
make check       # Tests, shell syntax, source links and all six Compose profiles
```

`make check` needs Python 3 and Compose v2, starts no containers and uses
`.env.example` instead of your private `.env` for Compose validation.

`make health`, `make smoke` and `make wait` accept `PROFILE=core|ai|reviews|demo|full|observability`
(default: `ai`, matching `make up`). For example, `make health PROFILE=core` checks
Kafka and Explorer without requiring the Agent. Checks fail with exit code 1 if
an expected container is missing/unhealthy or its HTTP/broker probe fails;
unknown profiles return 2. `demo` adds AutoTune, `full` adds Spectra, and
`observability` adds Prometheus/Grafana. Chroma is checked through its container
state/health when present; model installation and a successful LLM inference
are separate checks. `make demo` stops on core readiness failure and finishes
with a full-profile health check.
Use `make down` for the core stack, `make hub-down` for the full stack, or
`make observability-down` for the observability profile. `make reset` removes
core Kafka and operational-review volumes, including their stored data.

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
make report PROFILE=demo
```

Scenario guides are kept under `scenarios/`: `basic`, `consumer-lag`, `invalid-records` and `overload`. Each guide describes what the scenario injects and what to inspect. Run `SCENARIO=lag make scenario-assert` to execute a scenario with machine-checkable assertions. `make agent-e2e` additionally checks an actual Agent → Explorer MCP tool call when a model provider is configured.

### 🔎 Review lag, topic rules and dead letters

KafkaExplorer now offers read-only MCP tools for topic configuration and
environment-specific policy checks, comparisons of two complete consumer-lag
readings, and DLQ reviews with declared source/retry/replay references. Kex-anHarness
can use them while distinguishing measured Kafka evidence from configured
expectations. For the **one-broker Lab**, an optional profile declares a `lab`
policy (one replica, one in-sync replica), maps the demo DLT to its source,
and persists lag baselines in Explorer's `/app/data` volume:

```bash
# The compatibility manifest selects Explorer 2.1.1 and Agent 0.9.16.
make profile-reviews
```

Check the review tools in Explorer's MCP catalog before using the new prompts.
The Lab does not claim that injecting a malformed source record automatically
populates the DLT.
See [the walkthrough and image versions](docs/OPERATIONAL-REVIEWS.md).

```bash
make report PROFILE=demo
```

### 🧭 Choose a deployment profile

| Goal | Command | Components |
|---|---|---|
| Inspect Kafka | `make profile-core` | Kafka + Explorer |
| Add governed AI diagnosis | `make profile-ai` | Kafka + Explorer + Agent |
| Evaluate operational reviews | `make profile-reviews` | Kafka + Explorer + Agent with optional `lab` policy, DLT source declaration and persisted lag baseline |
| Run the complete published stack | `make profile-full` | Kafka + Explorer + Agent + AutoTune + Spectra |
| Run the guided scenario | `make profile-demo` | Full stack + readiness + traffic + health view |

The compatible image set is centralized in `versions.env`, which acts as the Lab
compatibility manifest. AutoTune and both Spectra images use immutable registry
digests, also used as Compose defaults. Their digests were resolved from the
published `latest` references on 2026-10-17. To update them, inspect the intended
release with `docker buildx imagetools inspect <image>:<tag>`, update both the
manifest and the Compose fallback, then run `make check` and the integration
smoke test. AutoTune's pinned index currently contains `linux/amd64`; Spectra's
indices contain both `linux/amd64` and `linux/arm64`.

### 📦 Prefer a smaller starting point?

For Kafka + Explorer + Kex-anHarness:

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
| [Kex-anHarness](https://github.com/devdownin/Kex-anHarness) | Uses governed actions, supervision and human approval; interprets Explorer's lag, policy and DLQ evidence through MCP |
| [Kafka SQL Explorer](https://github.com/devdownin/Kafkaexplorer) | Inspects, queries, traces and audits Kafka; exposes read-only operational reviews and configurable topic expectations |
| [KafkaConsumerAutoTune](https://github.com/devdownin/kafkaconsumerautotune) | Consumes Kafka traffic and adapts consumer settings using PID-based tuning, with resilience and observability |
| [SpectraLLM](https://github.com/devdownin/SpectraLLM) | Provides optional private local RAG, document ingestion, fine-tuning and local LLM serving |

## 🏗️ How it connects

The [architecture diagram](docs/assets/kex-lab-architecture.png) summarizes the
core data and tool paths. Solid arrows show event flow and MCP tool calls;
the dashed SpectraLLM connection represents an optional integration that must
be configured explicitly. The `kafka-init` service creates topics and seeds
records before dependent applications start.

**Runtime boundaries:** Kafka is the shared event backbone; Explorer owns inspection and the read-only MCP evidence boundary; AutoTune consumes Kafka traffic and adapts its consumer settings; Kex-anHarness reasons over governed MCP evidence rather than receiving Kafka mutation rights; Spectra is optional local inference/knowledge infrastructure. See [the detailed architecture](docs/ARCHITECTURE.md).

## 📊 Evaluate with evidence

Individual products can also be evaluated from their upstream repositories. `make components` clones them under `.components/`; then run `sh scripts/evaluate.sh <component>`.

For the integrated Lab, optional cross-project observability is available with:

```bash
make health PROFILE=demo
# Containers, Kafka, Explorer, Agent and AutoTune readiness

make observability-up
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000
# Dashboard: Kex Lab / Kex Lab — Integrated Operations
# Direct link: http://localhost:3000/d/kex-lab-operations
```

Image versions are centralized in `versions.env`. See [docs/EVALUATION.md](docs/EVALUATION.md) for evaluation paths, [docs/END-TO-END.md](docs/END-TO-END.md) for the traffic-to-diagnosis demo, [docs/OPERATIONAL-REVIEWS.md](docs/OPERATIONAL-REVIEWS.md) for the new MCP reviews, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for architecture, [docs/CONTRACTS.md](docs/CONTRACTS.md) for integration boundaries and [docs/SCORECARD.md](docs/SCORECARD.md) for the evidence checklist.

The dashboard distinguishes scrape availability from application health and
shows AutoTune traffic, errors/retries, batch duration, JVM usage and measured
AutoTune consumer lag. Missing counters or failed lag probes stay unavailable;
they are not replaced with zero. Lag is for AutoTune's consumers, not every Kafka
group. See [the observability guide](docs/OBSERVABILITY.md).

`make report PROFILE=observability` snapshots the current runtime image IDs and
registry digests, health probes, interface links and the latest recorded
assertion per scenario for the same project/topic. Assertions include their
recording date, source commit and worktree state; reporting does not rerun them.
The command still writes Markdown/JSON when checks fail and returns nonzero for
failed health, collection errors or a latest failed assertion. It records no
application record payloads or configuration credentials.

## 🏷️ Releases

Kex Lab versions the **integration bundle**, independently from its component
release cycles. `VERSION` selects the Lab version (`0.1.0`); `versions.env`
records component image references.

```bash
make check
make integration-smoke
make observability-smoke
make release-prepare  # Requires a clean, committed worktree
```

Release preparation builds the exact Git commit into `dist/kex-lab-0.1.0.tar.gz`,
with `bundle.json`, `versions.env`, release notes and `SHA256SUMS`. The archive
excludes local credentials, reports, component checkouts and model artifacts.
After the PR is merged, a matching `v0.1.0` tag triggers the release workflow,
which requires main ancestry and passing checks before publishing.
See [release instructions](docs/RELEASING.md) and [0.1.0 notes](docs/releases/v0.1.0.md).

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
│   ├── kafka-init.sh
│   ├── quick-demo.sh
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

### Agent repository name

The Kex-anHarness source repository is
[devdownin/Kex-anHarness](https://github.com/devdownin/Kex-anHarness).
`make components` checks it out under `.components/Kex-anHarness`. The published
Docker image remains `compagnonsdudev/kex-agent-ai`; the Lab keeps the compatible
image version pinned in `versions.env`.

Existing `.components/Kex-agent-ai` checkouts are moved to `.components/Kex-anHarness`
by `make components`, preserving local files and Git history. If both directories
already exist, both are kept and the new one is used. The agent remote is updated
to the new URL before the normal fast-forward-only update.

### Isolated integration smoke test

`make integration-smoke` creates a unique `kex-lab-test-*` Compose project, uses
loopback ports assigned by Docker, and checks basic and DLT traffic increases.
It ignores an inherited `COMPOSE_PROJECT_NAME` and port settings for isolation.
On success, failure or a handled signal, it removes only that test project's
containers, network and volumes. Logs are printed before cleanup on failure.
A forced kill or machine crash can leave test resources behind; inspect their
project label before cleanup. The normal Lab project and volumes are preserved.
