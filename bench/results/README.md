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

## Export to Hugging Face (`kvwire export`, ADR-0007)

`kvwire export --runs bench/results/<run_id> ... --out <dir>` builds the
`rdma-kv-transfer-traces` dataset (six configs) and its card. It reads these files when
present; `manifest.json` is required:

```
<run_id>/
  manifest.json                 + gpudirect_mode, pcie_topo_hash, is_rxe (EnvironmentRow)
  ceiling/ceilings.csv          nic,message_bytes,n_qps,memory,bw_gb_per_s,lat_us
  transfers_raw.csv             TransferKey columns + rep,total_bytes,duration_ns,cpu_ns
  prefill.csv                   model,context_len,batch,tp,gpu,rep,duration_ms
  transfer_events.jsonl         TransferEvent; detail carries req_id and layer
  prefill_layers.jsonl          {req_id, transfer_id, layer, start_ns, end_ns}
```

Validation runs first and blocks writing on any error: unknown run id or env hash, a
transfer without a same-config ceiling, SoftRoCE rows in a main config, undeclared units.
`--push` uploads only after you type the repo id. Columns and units:
`kvwire/export/rows.py`.
