# bench/results/

One directory per run: `bench/results/<run_id>/` (UTC timestamp id). Raw data is gitignored;
commit only curated summaries, and only with their manifest.

```
<run_id>/
  config.yaml           exact scenario used
  manifest.json         GPU, driver, CUDA, vLLM commit, Triton, NIC model+fw, rdma-core/OFED,
                        kernel, GPUDirect mode, PCIe topology hash, NCCL/UCX/NIXL versions
  ceiling/              perftest sweep used to normalise this run's transport numbers
  timelines.jsonl       RequestTimeline records
  transport.csv         per-strategy transport stats
  faults.jsonl          faultlab ledger (fault runs only)
  report/               generated plots + summary.md
```

Every number in README/docs/blog links here. No run id, no number.
