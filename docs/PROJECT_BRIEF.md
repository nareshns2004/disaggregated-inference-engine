# Project Brief — kvwire

## 1. One-line pitch

Split LLM serving into prefill and decode GPU pools. Move the KV cache between them over
GPUDirect RDMA at near line rate, hidden behind prefill compute. Keep every request
correct and alive when a node, link, or queue pair fails mid-transfer. Publish measured
evidence of when this beats colocated serving and when it doesn't.

## 2. The problem

- **Interference.** Prefill is compute-bound and bursty; decode is memory-bandwidth-bound
  and latency-sensitive. Colocating them means a long prompt's prefill stalls every
  in-flight decode (TPOT spikes), or decode batching delays new prefills (TTFT spikes).
  Chunked prefill reduces this but does not remove it.
- **Disaggregation fixes interference but creates a data-movement problem.** The KV cache
  must cross the network, and it is large. Calculation for Llama-3.1-8B (32 layers, 8 KV
  heads, head_dim 128, bf16): 2 × 32 × 8 × 128 × 2 B = 128 KiB per token, so a
  4K-token prompt is ~512 MiB. For a 70B-class model (80 layers, 8 KV heads) it is
  ~320 KiB per token. Verify these against the model configs you actually use.
- **The messages are small and scattered.** Paged KV means per-layer, per-block chunks.
  For the 8B model with 16-token blocks, that is 16 × 2 × 8 × 128 × 2 B = 64 KiB per
  layer per block. Moving these at line rate is a small-message, many-work-request,
  scatter-gather problem, not a bulk `memcpy`. This is exactly where RDMA expertise shows.
- **Failure semantics are hard and usually unaddressed.** A late RDMA write into a KV
  block that has since been freed and reused silently corrupts another request's
  output. QPs enter error states. Orphaned KV leaks memory on the prefill side. Most
  public systems report throughput, not behavior under fault.

Prior art to master and cite (verify details and record them in `docs/prior_art.md` in
M1): DistServe (OSDI '24; goodput under SLO as the metric), Splitwise (ISCA '24),
Mooncake (FAST '25; KV-centric disaggregation and a transfer engine), TetriInfer, NVIDIA
Dynamo and NIXL, vLLM's disaggregated prefill / KV connector framework, SGLang PD
disaggregation, LMCache, llm-d, and Sarathi-Serve (chunked prefill, the strongest
colocated baseline).

## 3. Positioning — the honest version

Disaggregated serving is crowded. A from-scratch "engine" is a me-too and cannot win on
features. The defensible contribution is narrower and deeper:

| Area | Existing work | What kvwire adds |
|---|---|---|
| Engine | vLLM, SGLang, Dynamo | Nothing. We plug into vLLM. |
| KV transport | NIXL, Mooncake transfer engine, UCX, LMCache | A verbs-level transport tuned for paged small messages (WR batching, SGE lists, doorbell coalescing, multi-rail, layer-wise streaming), with explicit **stale-write fencing** and QP error recovery; measured as % of line rate vs NIXL/TCP |
| Heterogeneous layouts | Handled in some systems, sparsely documented | A Triton re-layout kernel for prefill TP ≠ decode TP and block-size mismatch, pack/unpack fused with the transport's send/recv buffers |
| Failure behavior | Rarely measured publicly | Fault matrix, request success rate under fault, zero-corruption verification |
| Evaluation | Papers pick favorable regimes | Crossover analysis: which workloads disaggregation wins or loses vs chunked-prefill colocated serving |

If the M1 review shows NIXL or Mooncake already covers stale-write fencing and fault
recovery with published measurements, re-scope toward whichever gap remains. Do not
build a me-too.

## 4. Thesis

    TTFT_disagg ≈ queue_p + prefill + exposed_transfer + queue_d + first_decode_step

With layer-wise streaming, KV for layer *l* is sent while layer *l+1* computes, so
`exposed_transfer` shrinks to roughly the last layer's transfer plus completion
signaling. The transport's job is to make that residual small and stable at p99, using
small scattered messages, under contention, and while hardware fails.

Hypotheses to confirm or refute with data:
- **H1.** At realistic block sizes, a naive per-block RDMA WRITE reaches well under line
  rate. WR batching and SGE coalescing (or packing via the kernel) close most of the gap.
- **H2.** With layer-wise streaming, exposed transfer is a small fraction of TTFT for
  prompts ≥ 1K tokens on RDMA. It is not small on TCP.
- **H3.** Disaggregation beats chunked-prefill colocated serving on goodput-per-GPU only
  when prompts are long relative to outputs and TPOT SLOs are tight. The crossover is
  measurable.

## 5. Objectives

- **O1 Baselines and ceilings.** Colocated vLLM (with and without chunked prefill), vLLM
  with a reference disaggregated connector (NIXL or similar), and hardware ceilings from
  perftest.
- **O2 Transport.** A GPUDirect RDMA KV transport (C++, pybind11) with layer-wise
  streaming, multi-rail, and small-message optimization, plus a TCP variant as a control.
- **O3 Integration.** Prefill/decode pools running under vLLM through its KV connector
  interface, with a coordinator that routes requests and manages transfers.
- **O4 Re-layout kernel.** A Triton kernel for heterogeneous TP and block layouts,
  profiled with Nsight. It ships only if it earns its place.
- **O5 Failure-aware coordination.** Detection of and recovery from the faults in the
  fault matrix, with fencing that guarantees no stale writes, and request success
  measured under fault.
- **O6 SLO-aware scheduling and goodput.** Admission and routing that maximize
  requests/s meeting TTFT and TPOT SLOs, evaluated against baselines across a workload
  sweep.

## 6. Measurable outcomes

Targets are hypotheses, revised with M1 data via an ADR. Definitions live in
`docs/EVALUATION.md`.

| # | Metric | Target (initial) | Compared against |
|---|---|---|---|
| 1 | KV transport throughput, paged per-layer messages, GPU→GPU | ≥ 85% of `ib_write_bw` at the equivalent aggregate size; efficiency-vs-message-size curve published | perftest ceiling; NIXL; naive per-block WRITE |
| 2 | Single-transfer latency (one layer-block batch) | p99 within 1.5× of `ib_write_lat` + size/bandwidth | perftest |
| 3 | Exposed transfer in TTFT, prompts ≥ 1K tokens | ≤ 10% of TTFT at p50, reported at p99 | TCP transport; reference connector |
| 4 | TTFT p50/p99 | Lower than the TCP variant at every prompt length ≥ 1K tokens; gap quantified | kvwire-TCP, reference connector |
| 5 | Goodput (max req/s at ≥ 90% SLO attainment) per GPU | ≥ colocated chunked-prefill in the long-prompt/tight-TPOT regime; crossover plot across the sweep | vLLM colocated (chunked prefill on) |
| 6 | Request success rate under the fault schedule | ≥ 99.9% completed; failed requests fail fast with a clear error | Reference connector under the same faults |
| 7 | Output corruption | Zero token mismatches under greedy decoding vs reference across all fault runs | Colocated reference outputs |
| 8 | In-flight request recovery time after decode-node loss | p99 reported; target set after M1 | Reference connector |
| 9 | Transport CPU cost | ≤ 1 core per NIC at line rate | Reference connector |
| 10 | Re-layout kernel | ≥ 80% of DRAM-bandwidth roofline for the pack/unpack; net TTFT improvement or it is not merged | PyTorch reference; SGE-only path |

## 7. Non-goals

- Not a new engine, scheduler framework, model runtime, or attention kernel. FlashAttention
  and FlashInfer are not being competed with.
- No speculative decoding, quantization research, or prefix-cache-aware routing (Stretch
  at most).
- No claims beyond the scale actually run.

## 8. Scope tiers

- **Must:** baselines and ceilings; verbs transport with GPUDirect, layer-wise streaming,
  WR batching, stale-write fencing, and QP error recovery; TCP variant; vLLM connector
  integration; coordinator with routing and failure handling; fault matrix Must rows;
  goodput/SLO evaluation with a crossover sweep; correctness gate; write-up.
- **Should:** multi-rail striping; Triton re-layout kernel for heterogeneous TP;
  SLO-aware admission; dynamic prefill:decode ratio recommendation from the sweep;
  Grafana dashboards.
- **Stretch:** dynamic pool rebalancing online; prefix-cache-aware routing; MoE model; a
  shared transport library with goodput (checkpoint replication); RDMA weight sync from
  trainer to inference fleet for RL post-training (the parked idea, gated on Must results).

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| vLLM connector API churns | Pin the vLLM version; keep a thin adapter layer; ADR-0001 |
| GPUDirect RDMA not working (ACS/IOMMU, peermem/dmabuf, BAR1, PCIe topology) | M1 bring-up with perftest `--use_cuda`; document `nvidia-smi topo -m`; a host-staging fallback clearly labeled |
| NIXL already solves it | M1 prior-art gate; compare, then publish the delta, whether positive or negative |
| Disaggregation loses on your workloads | That is a result: publish the crossover plot |
| Scale too small (few nodes) | Report per-GPU goodput; contention experiments; projection only if labeled |
| Employer IP overlap with the internal POC | Clean-room rule; written clearance before the public push |
| The kernel becomes a vanity item | ADR-0003 gate: merge only on measured net win |
| Claude Code writes code Naresh can't defend | `[OWNER-CORE]` plus `/drill` |

## 10. Public deliverables (M6)

- README with the three headline numbers, each shown against its ceiling and baseline.
- Transport design doc.
- Crossover plot.
- Fault results.
- Blog post ("Moving KV cache at line rate, and what happens when it fails").
- Demo recording: live TTFT/TPOT dashboard while a decode node is killed.
- Every number linked to a run id.
