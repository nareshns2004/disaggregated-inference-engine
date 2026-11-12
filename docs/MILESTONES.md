# Milestones — kvwire

A milestone closes only when its exit criteria are met with evidence (run ids, test names,
docs), not when its code is written.

The order is deliberate. The RDMA transport comes second (M2), straight after baselines,
because it is the core contribution and the riskiest dependency. The Triton work is a **KV
re-layout (pack/unpack) kernel** in M4, gated on a measured net win (ADR-0003), not a fused
attention kernel: re-layout is something disaggregation itself requires, while attention
kernels are already well served by FlashAttention and FlashInfer.

`[OWNER-CORE]` = a maintainer implements; other contributors (human or AI) design
interfaces, write tests and benchmarks, and review.

---

## M1 — Baselines, ceilings, harness, prior-art gate

**Deliverables**
- Repo scaffold and CI *(done)*; env manifest *(done)*; `make topo` (GPU↔NIC affinity).
- GPUDirect bring-up: perftest `--use_cuda` sweep → `make ceiling` artifacts.
- Load generator and request-timeline capture; SLO definitions per model.
- C0 and C1 baselines (vLLM colocated) at the pinned vLLM version: TTFT, TPOT, goodput.
- D0 reference disaggregated baseline running, or a documented reason it can't.
- KV-size calculator (per model, per layout) *(done)*; message-size profile of real
  requests; the pinned vLLM attention backend's K/V layout confirmed (separate vs
  interleaved decides region size and count).
- SLO values pinned per model **before** C0 runs.
- `docs/prior_art.md`, covering:
  - DistServe, Splitwise, Mooncake, NIXL/Dynamo, vLLM KV connectors, SGLang PD,
    Sarathi-Serve
  - for each one: its mechanism, its gap, and what kvwire reuses
  - a go/re-scope decision on the fencing and fault-behavior gap

**Exit**
- Ceilings recorded, including the efficiency-vs-message-size curve for `ib_write_bw`
  (decides the regime in which H1 is tested).
- C0 goodput curve for ≥ 2 workloads.
- ADRs 0001–0004 accepted or revised.
- Prior-art go/re-scope decision written.
- Brief §6 targets revised with data.

`[OWNER-CORE]`: GPUDirect bring-up diagnosis; the prior-art gap analysis.

## M2 — RDMA KV transport (C++)

**Deliverables**
- **First experiment:** does type-2 MW bind work over GPU MRs (dmabuf/peermem) on the
  target NIC, firmware and driver, and what does a bind cost? The answer decides ADR-0005.
- Verbs lifecycle with RAII; whole-pool MR registration; GPUDirect (dmabuf or peermem).
- The four small-message strategies (TRANSPORT §4) behind one interface; C++
  microbenchmarks vs the ceiling.
- Completion signaling; epoch fencing prototype; QP error reset path.
- TCP variant behind the same interface.
- pybind11 bindings.
- Loopback/rxe logic tests, plus two-node GPU tests.

**Exit**
- Brief metrics #1, #2, and #9 measured for every strategy.
- The efficiency-vs-size plot exists.
- K06 and K07 pass in isolation, with zero corruption (K07 with ≥ 2 rails).
- ADR-0005 accepted with measured bind/reset cost.

`[OWNER-CORE]`: QP state machine and error handling; the WR batching/signaling path; the
fencing mechanism.

## M3 — Prefill/decode split, integrated

**Deliverables**
- vLLM connector (send and receive) using the transport.
- Layer-wise streaming triggered by per-layer CUDA events.
- Router/coordinator with the transfer registry and state machine, plus basic routing.
- End-to-end correctness gate (greedy output match) in CI on GPU runners.
- Design doc for the P/D split and the coordinator.

**Exit**
- Brief metrics #3 and #4 measured (D1 vs D3 vs D0).
- TTFT decomposition plot.
- The correctness gate is green.

`[OWNER-CORE]`: layer-wise trigger and overlap logic (the vLLM integration is shared work,
reviewed by the maintainer).

## M4 — KV re-layout kernel (Triton), gated

**Deliverables**
- Pack/unpack kernels for block gather and for TP re-partitioning.
- PyTorch reference and exhaustive shape tests.
- Nsight Compute and Nsight Systems profiles.
- Integration as strategy (c) and for heterogeneous TP.

**Exit**
- Brief metric #10 measured.
- ADR-0003 gate decided with data: merge, or document why not.

`[OWNER-CORE]`: the kernel itself.

## M5 — Failure-aware coordination + SLO-aware scheduling + goodput evaluation

**Deliverables**
- Fault matrix Must rows are injectable, detected, and recovered.
- Leak detectors.
- SLO-aware admission and routing (Should).
- P:D ratio sweep.
- The full evaluation grid from EVALUATION §3–4.

**Exit**
- Brief metrics #5–#8 measured.
- Crossover heatmap, including the regimes where disaggregation loses.
- Zero corruption across all fault runs.
- H1–H3 each confirmed or refuted in writing.

`[OWNER-CORE]`: the abort/fence/retry state machine; the admission policy.

## M6 — Write-up and release

**Deliverables**
- README (three headline numbers, each against its ceiling and baseline).
- Transport design doc (polished TRANSPORT.md).
- Results report.
- Blog post.
- Demo recording: kill a decode node live; dashboards stay correct.
- Clean-room check: no third-party proprietary material; publication clearance for all
  hardware-derived data.
- First tagged release (`v0.1.0`) with a CHANGELOG entry.

**Exit**
- Every public number links to a run id.
- The "where disaggregation loses" section is in the README and the report, not trimmed.
- An outside reviewer can reproduce the ceiling sweep and one D1-vs-D3 TTFT comparison
  from the README.
