# ADR-0001: Corpus scale

**Status:** Accepted
**Date:** 2026-08-31

## Context

The Kestrel specification targets a corpus of 10–15M chunks, forcing real sharding
because a single node no longer fits comfortably.

The development machine is a laptop with 15.9 GB of RAM. WSL2 is capped at 11 GB
(see `.wslconfig`), and that 11 GB must also host Postgres, Redpanda, MinIO,
Prometheus, Grafana, and Jaeger alongside the shards — roughly 3–4 GB of
supporting infrastructure, leaving about 7 GB for index data.

Chunks are embedded with bge-small-en-v1.5, which produces 384-dimensional vectors.

### Memory arithmetic

Per vector, 384 dimensions:

| Storage | Bytes/vector |
|---|---|
| fp32 | 1,536 |
| fp16 | 768 |
| int8 | 384 |
| PQ (m=48) | 48 |

At the specification's target:

- 12M chunks, fp32: **18.4 GB** of vectors alone — larger than the entire WSL allocation.

At a revised target of 2M chunks:

- fp32 vectors: 3.07 GB
- int8 vectors: 768 MB
- HNSW graph at M=16 (~32 links/node × 4 bytes): 256 MB
- **int8 vectors + graph: ~1.0 GB**, or roughly **170 MB per shard across 6 shards**

## Decision

Target a corpus of **~2–3M chunks** rather than 10–15M.

This figure is an estimate. Week 3 will measure the actual chunk count produced by
the Server Fault dump plus the documentation sources, and will supersede it.

## Alternatives considered

**Keep 12M chunks, accept disk-backed search.** Rejected: paging index data from
disk would dominate latency and make the p99 measurements — the core of the
project — meaningless.

**Keep 12M chunks, use aggressive PQ throughout.** Rejected: it fixes quantisation
at the most lossy setting, removing the axis the tuner is supposed to search.

**Rent cloud hardware to hit 12M.** Rejected: the project runs at ₹0, and the
scale would not change any conclusion the project draws.

## Consequences

**The memory constraint becomes real.** The tuner's objective is to maximise
nDCG@10 subject to p95 ≤ 150 ms and RSS ≤ B per shard. On hardware with abundant
memory that constraint is decorative — every configuration satisfies it, and the
quantisation axis never has to justify itself. At 170 MB per shard it binds:
configurations genuinely fail it, and the tuner must trade recall against memory.
That is the tradeoff a constrained optimisation problem is supposed to contain.

**Sharding remains justified.** 6 shards at ~170 MB each is a genuine
scatter-gather system, and every distributed mechanism — fanout, hedging, deadline
propagation — behaves the same regardless of absolute corpus size.

**Reported figures must say 2M, not 12M.** The resume bullet, README, and any
write-up quote the measured corpus size. A precise modest number is worth more
than an impressive one that does not survive questioning.

**Absolute recall numbers are not comparable to published results** on larger
corpora. All comparisons in this project are internal: against the pgvector
baseline on the same corpus.
