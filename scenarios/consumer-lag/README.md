# Consumer lag

Injects a larger burst (10,000 records by default) to make consumer backlog and adaptation easier to observe.

```bash
make demo-lag
```

Observe the consumer group in Kafka SQL Explorer and the AutoTune dashboard. The scenario creates load; the resulting lag depends on the runtime and consumer throughput.

With compatible Explorer and Agent images and the optional
[`profile-reviews`](../../docs/OPERATIONAL-REVIEWS.md), ask for
`kex_consumer_lag_trend` on the actual AutoTune group twice. Only two complete
readings can establish a measured change; the shared baseline survives an
Explorer restart when the overlay's volume is mounted.
