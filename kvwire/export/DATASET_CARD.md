---
license: cc-by-4.0
pretty_name: RDMA KV-Transfer Traces
tags:
  - rdma
  - gpudirect
  - kv-cache
  - disaggregated-inference
  - llm-serving
configs:
{{configs_yaml}}
---

# RDMA KV-Transfer Traces

Measured KV-cache transfers between prefill and decode GPUs over RDMA, with the perftest
ceiling for every configuration, the prefill time needed to recompute instead, and the
hardware each row came from. It answers one question: **at a given model, context length
and fabric, is moving the KV cache cheaper than recomputing it, and how much of the move
is hidden behind prefill compute?**

Produced by [kvwire](https://github.com/nareshns2004/disaggregated-inference-engine)
(GitHub Project 2) at commit `{{kvwire_commit}}`, from runs
{{run_ids}}. Explored in the
[disagg-kv-explorer](https://huggingface.co/spaces/nareshns2004/disagg-kv-explorer) Space.

## Hardware and software

{{environments_table}}

## Method

- **Ceilings first.** A `perftest` (`ib_write_bw --use_cuda`) sweep on the same NIC,
  message size, QP count and memory mode runs before any transfer is measured. No transfer
  row exists without a matching ceiling.
- **Efficiency, two denominators.** `efficiency_vs_region_ceiling` divides by the ceiling at
  the transfer's own message size; `efficiency_vs_peak` divides by the large-message peak
  (true line rate). Multi-rail rows scale both by the number of rails.
- **Repetitions.** At least 10 after warmup per point. p50/p99 use the nearest-rank method;
  with fewer than 100 repetitions p99 is close to the maximum.
- **Prefill is measured,** not estimated from FLOPs, at the same model, context and batch.
- **Provenance.** SoftRoCE (`rxe`) runs never enter these configs (they are logic tests).
  Host-staging fallback rows have `host_staging = true`.

## Configs and columns

| Config | One row is |
|---|---|
| `transfers` | one transfer configuration, aggregated over repetitions |
| `transfers_raw` | one repetition, for your own statistics |
| `layer_timelines` | one (request, layer): prefill window and send/commit times |
| `ceilings` | one perftest point |
| `prefill` | one prefill timing configuration |
| `environments` | one hardware/software setup (`env_hash` joins everything) |

{{column_table}}

## Limitations

- Small scale: {{n_envs}} hardware configuration(s). Results do not generalise to other NIC
  models, firmware, PCIe topologies or switch configurations.
- `layer_timelines` timestamps are CLOCK_MONOTONIC on the prefill host: comparable with each
  other, not across hosts.
- No serving results (TTFT, goodput, SLO attainment) are in this dataset; those live in
  kvwire's reports.

## Reproduce

```
git clone https://github.com/nareshns2004/disaggregated-inference-engine && cd disaggregated-inference-engine
git checkout {{kvwire_commit}}
make ceiling                                   # perftest sweep
make bench SCENARIO=bench/scenarios/<x>.yaml   # transfers, prefill, timelines
kvwire export --runs bench/results/<run_id> --out out/   # validates before writing
```

## Licence and citation

Data: CC-BY-4.0. Code that produced it: Apache-2.0.
