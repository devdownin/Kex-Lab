# Invalid records / DLT path

Injects the normal sample plus deliberately invalid input.

```bash
make demo-dlt
```

Use this scenario to inspect how the integrated components expose malformed input and any dead-letter handling provided by the running consumer configuration.

The invalid record is injected into the source topic. It reaches the DLT only
if a consumer is configured to route failures there. With the optional
[operational review profile](../../docs/OPERATIONAL-REVIEWS.md),
`kex_dlq_review` identifies the **declared** source and checks observable
Kafka state; an empty DLT does not prove any retry or replay capability.
