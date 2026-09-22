# End-to-end scenario

This scenario demonstrates the operational chain shared by three of the four projects without duplicating their source trees.

```text
traffic generator
       |
       v
    Kafka 4.3 <--------- KafkaConsumerAutoTune
       |
       v
Kafka SQL Explorer --MCP--> Kex Agent AI
       ^
       |
 optional private AI / knowledge
       |
   SpectraLLM
```

## Run

Configure `.env`, including an LLM key if you want the Agent reasoning step, then:

```bash
make demo
```

Compose first runs the one-shot `kafka-init` service. It creates `demo.app.topic` and `demo.app.topic.dlt` (six partitions by default) and seeds `demo.app.topic` with 500 deterministic JSON records by default. Kafka-dependent services then start after successful initialization. Values can be changed through `KEX_LAB_TOPIC`, `KEX_LAB_DLT_TOPIC`, `KEX_LAB_PARTITIONS` and `KEX_LAB_MESSAGES`.

AutoTune is launched with its `dev` profile and H2 persistence, so the Lab does not require the Oracle XE stack merely to demonstrate Kafka consumption and tuning. Its image normally waits for Oracle in its entrypoint; the Lab overrides that entrypoint for this H2 evaluation profile.

## Observe

Open:

- Explorer: http://localhost:8080
- Agent: http://localhost:8081
- AutoTune: http://localhost:8082/dashboard

In AutoTune, observe throughput, lag and optimizer state. In Explorer, inspect `demo.app.topic`, its records and consumer groups.

Then ask the Agent:

> Inspect demo.app.topic and tell me whether its consumers are keeping up. Base the answer on the Kafka tools.

The expected proof is a chain of evidence rather than a predetermined prose answer: the Agent should invoke Explorer's MCP tools, Explorer should read the same Kafka broker, and the resulting state should correspond to the consumer activity visible in AutoTune.

## Change the load

```bash
KEX_LAB_MESSAGES=5000 make traffic
```

The `traffic` service uses the same `scripts/kafka-init.sh` implementation as Compose startup, so this adds another 5,000 deterministic records without maintaining a separate producer path. This gives the optimizer a larger backlog to work through. Compare consumer lag in Explorer with throughput and tuning interventions in AutoTune.

## SpectraLLM

SpectraLLM remains optional because its first boot downloads several GB of model weights. It is complementary in two roles already supported by the upstream projects: private/local LLM inference and private domain knowledge/RAG. Run it with:

```bash
./scripts/evaluate.sh spectra
```

It is intentionally not a hard dependency of the traffic-to-diagnosis path. This keeps `make demo` suitable for a normal Docker workstation and makes the additional private-AI layer an explicit evaluation choice.

## Stop

```bash
make demo-down
```

Use `make reset` for the core stack and volumes.
