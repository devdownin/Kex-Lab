# Kafka operational reviews in Kex Lab

KafkaExplorer exposes four read-only MCP reviews: topic configuration,
`kex_topic_policy_review`, `kex_consumer_lag_trend` and `kex_dlq_review`.
Kex Agent AI has guidance for interpreting their evidence, missing policies and
declarations. This Lab provides an **optional** configuration for its single broker.

## Image compatibility

The `latest` Docker Hub tags in `versions.env` are moving references. At the time
this Lab guide was updated, they predated the upstream operational review changes.
Select Explorer and Agent images built from revisions containing those changes
([Explorer PR #426](https://github.com/devdownin/Kafkaexplorer/pull/426),
[Agent PR #129](https://github.com/devdownin/Kex-agent-ai/pull/129)) before trying
the walkthrough. Set `EXPLORER_IMAGE` and `KEX_AGENT_IMAGE` in `.env` to their
released tags or pinned digests; publishing a Docker Hub description does not
update an image. Confirm `kex_topic_policy_review`, `kex_consumer_lag_trend` and
`kex_dlq_review` in Explorer's **MCP** tool catalog. If they are missing, update
the image references; the Lab does not simulate their answers.

Until compatible published images are available, you can build the merged
upstream `main` branches locally and use those tags in `.env`:

```bash
git clone --depth 1 https://github.com/devdownin/Kafkaexplorer.git ../Kafkaexplorer
docker build -t kex-lab-explorer:reviews ../Kafkaexplorer
git clone --depth 1 https://github.com/devdownin/Kex-agent-ai.git ../Kex-agent-ai
docker build -t kex-lab-agent:reviews ../Kex-agent-ai
# In .env: EXPLORER_IMAGE=kex-lab-explorer:reviews
# In .env: KEX_AGENT_IMAGE=kex-lab-agent:reviews
```

## Start the optional profile

```bash
cp .env.example .env
# Edit .env: replace the development tokens and select compatible image references.
make profile-reviews
```

The overlay `compose.operational-reviews.yml` mounts a named `/app/data` volume and
sets `EXPLORER_MCP_LAG_HISTORY_DIRECTORY=/app/data/mcp-lag-history`. The lag
baseline then survives container restarts. A first reading has no trend; a
second **complete** reading for the same topic and group is needed. Its default
validity is 48 hours. The local named volume serves one Docker host. For
several Explorer instances on different hosts, supply a shared writable
filesystem with interprocess locking at the same path on every instance.

The overlay also declares a `lab` topic policy of one replica and one
in-sync replica, suitable only for this **one-broker demo**, and an expected
`delete` cleanup policy. It applies to any topic reviewed as `lab`; never
treat this as a production resilience rule.
It declares `KEX_LAB_TOPIC` as the source of `KEX_LAB_DLT_TOPIC` and does not
claim a retry topic, monitored connector or replay runbook. The default topic
names come from `versions.env` and can be overridden in `.env`.

## Ask and inspect evidence

| Ask Kex Agent AI | Explorer tool | What to verify |
|---|---|---|
| “Does demo.app.topic meet the **lab** topic policy?” | `kex_topic_policy_review` | Measured replica/ISR counts and cleanup policy. An absent policy is `NOT_CONFIGURED`, never compliance. |
| “Is the consumer group on demo.app.topic falling behind since the last reading?” | `kex_consumer_lag_trend` | Supply an actual group ID from Explorer. Repeat after a second complete reading; missing baseline or offset resets mean the rate is unmeasured. |
| “Review demo.app.topic.dlt and its source.” | `kex_dlq_review` | The source is declared by the Lab; Kafka metadata and a bounded header sample are measured separately. Empty DLTs do not prove replay or monitoring works. |

`make demo-lag` produces a burst to observe consumer activity, whose lag
depends on throughput. `make demo-dlt` injects a malformed record into the
**source**; it does not guarantee a consumer routes it to the DLT. Check the
DLT's offsets before drawing a conclusion. `make agent-e2e` calls the current
`/api/agent/chat` route with the bearer token and requires an actual successful
Explorer tool call; it needs a configured model provider and Python 3.

The MCP path is read-only. Neither the agent nor the review tool replays a
record. The definitions, scopes and limitations are documented in
[KafkaExplorer's deployment reference](https://github.com/devdownin/Kafkaexplorer/blob/main/docs/DOCKERHUB-OPERATIONS.md#operational-mcp-reviews)
and the [agent MCP guide](https://github.com/devdownin/Kex-agent-ai/blob/main/docs/MCP.md).

Run `make down` to stop the core services while keeping the lag volume. `make
reset` deletes **all** Lab volumes, including broker data and the saved lag
baseline.
