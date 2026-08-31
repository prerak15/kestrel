# Kestrel

A distributed, self-tuning retrieval index for on-call incident knowledge.

**Status:** Week 1 — foundations. No retrieval results yet.

---

## What this is

When an on-call engineer is paged at 3 a.m. for a `CrashLoopBackOff`, a filling
write-ahead log, or an unhealthy etcd quorum, finding the relevant prior
post-mortem or runbook is slower than it should be — keyword search misses cases
where the same underlying issue was described with different terminology.

Kestrel is a self-hosted retrieval engine over that kind of corpus: Server Fault,
Unix & Linux, DBA and DevOps Stack Exchange sites, Kubernetes documentation,
Prometheus runbooks, and public incident write-ups. Documents range from 60-token
questions to 10,000-token runbooks full of YAML and tables, which is what makes
uniform chunking fail and makes the retrieval problem non-trivial.

It is a systems project that happens to be about retrieval, rather than an ML
project that happens to run on servers. The index is built here, not called over
an API — the engineering that interests me lives below the boundary most retrieval
projects treat as the floor.

## The three problems

**Retrieval quality** over a corpus spanning two orders of magnitude in document
length. Chunking strategy and hybrid sparse/dense retrieval are tuned, not assumed.

**Configuration search under a rebuild cost.** Roughly 10^7 index configurations
across chunking, embedding model, quantisation, index type, and fusion weights.
Each full evaluation costs an embedding pass plus an index build. Searched with
multi-fidelity Bayesian optimisation, using corpus fraction as the fidelity axis.

**Distributed serving under a p99 SLO.** Sharded scatter-gather search where the
router's tail latency is the tail of the *slowest* shard. Hedged requests,
deadline propagation, and shards that degrade `ef_search` to meet a deadline
rather than returning nothing.

## Architecture

```
                    ┌─────────────────────────────┐
                    │      Tuner (Ray Tune)       │
                    │  ASHA + BO over config space│
                    └──────────────┬──────────────┘
                                   │ winning config
                                   ▼
┌──────────────┐         ┌──────────────────────┐
│   Ingest     │ Redpanda│   Index Build (Ray)  │
│  (corpus +   ├────────►│  embed → cluster →   │
│   replay)    │         │  shard → build → S3  │
└──────────────┘         └──────────┬───────────┘
                                    │ segments
                                    ▼
                            ┌───────────────┐
                            │    MinIO      │
                            └───────┬───────┘
                                    │ pull
        ┌───────────────────────────┼───────────────────────┐
        ▼                           ▼                       ▼
  ┌───────────┐              ┌───────────┐            ┌───────────┐
  │ Shard 0   │              │ Shard 1   │    ...     │ Shard N   │
  │ (Rust)    │              │ (Rust)    │            │ (Rust)    │
  │ base+delta│              │ base+delta│            │ base+delta│
  └─────┬─────┘              └─────┬─────┘            └─────┬─────┘
        │         gRPC             │                        │
        └───────────────┬──────────┴────────────────────────┘
                        ▼
                ┌───────────────┐        ┌──────────┐
                │ Query Router  │◄──────►│  etcd    │
                │ (Rust)        │        │ routing  │
                │ - fanout      │        │  table   │
                │ - hedging     │        └──────────┘
                │ - merge/rerank│
                └───────┬───────┘
                        ▼
                 ┌─────────────┐
                 │ Eval Harness│──► Prometheus / Grafana / Jaeger
                 └─────────────┘
```

## Methodology

Every claim in this repository is a measured number with a bootstrapped 95%
confidence interval, produced by an evaluation harness validated against published
BEIR baselines before being trusted on this corpus.

- **Splits are temporal**, not random — near-duplicate questions would otherwise
  leak across train and test and inflate every metric.
- **Baselines are fair.** The control is pgvector with default HNSW parameters and
  fixed 512-token chunks, with those defaults recorded alongside every result.
- **Every result records its provenance** — git SHA, dirty-tree flag, CPU model,
  core count, kernel, and dataset version.

## Running it

Requires Linux (or WSL2), Docker, and [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:prerak15/kestrel.git
cd kestrel
uv sync
uv run pytest
```

## Repository layout

| Path | Contents |
|---|---|
| `eval/` | Evaluation harness — metrics, BEIR runners, result records |
| `tuner/` | Configuration space, index build pipeline, Ray Tune search |
| `shard/` | Rust shard server (from Week 13) |
| `router/` | Rust query router (from Week 16) |
| `deploy/` | Helm charts, k3d cluster config, Terraform |
| `bench/` | Load generators and latency analysis |
| `docs/adr/` | Architecture decision records |
| `docs/findings/` | Write-ups of experimental results |

## Scope and honesty

This runs on a single 16 GB laptop. The corpus is therefore ~2–3M chunks rather
than the 10–15M a dedicated cluster would allow — see
[ADR-0001](docs/adr/0001-corpus-scale.md). The shard cluster is CPU-pinned,
cgroup-limited containers on one host, not separate machines.

That setup produces valid results for hedging, fanout, and deadline propagation,
which are properties of response-time distributions. It cannot demonstrate real
network partitions, cross-AZ latency, or independent failure domains, and no claim
here depends on those.

## Data and attribution

Stack Exchange content is licensed CC BY-SA and used under those terms.
Documentation sources are pinned by commit SHA in `data/manifest.json`. No corpus
data is committed to this repository; the manifest records URLs and SHA256
checksums so the corpus can be reconstructed.

## Progress

- [x] Week 0 — Environment
- [x] Week 1 — Repository, CI, result provenance
- [ ] Weeks 2–3 — Corpus ingestion, labels, temporal split
- [ ] Weeks 4–5 — Evaluation harness, BEIR validation
- [ ] Weeks 6–7 — Observability, pgvector baseline
- [ ] Weeks 8–12 — Configuration space, Ray Tune, fidelity study
- [ ] Weeks 13–17 — Rust shard server, router, k3d cluster
- [ ] Weeks 18–22 — Load generation, semantic sharding, tail latency
