# Consumer lag

Injects a larger burst (10,000 records by default) to make consumer backlog and adaptation easier to observe.

```bash
make demo-lag
```

Observe the consumer group in Kafka SQL Explorer and the AutoTune dashboard. The scenario creates load; the resulting lag depends on the runtime and consumer throughput.
