# Milestones — kvwire

> **Framework edit vs the tracker (P2), proposed for approval.** The RDMA transport moves
> from M4 to M2, because it is the moat and the riskiest dependency. The Triton "fused
> attention" milestone becomes a **KV re-layout (pack/unpack) kernel** in M4, gated on a
> measured net win. Fused attention competes with FlashAttention/FlashInfer and would not
> survive "why didn't you just use FlashInfer?"; re-layout is required by disaggregation
> itself. Update the tracker once approved.

`[OWNER-CORE]` = Naresh implements; Claude Code designs interfaces, tests, and benchmarks,
and reviews.

---

## M1 — Baselines, ceilings, harness, prior-art gate

**Deliverables**
- Repo scaffold and CI; env manifest; `make topo` (GPU↔NIC affinity).
- GPUDirect bring-up: perftest `--use_cuda` sweep → `make ceiling` artifacts.
- Load generator and request-timeline capture; SLO definitions per model.
- C0 and C1 baselines (vLLM colocated) at the pinned vLLM version: TTFT, TPOT, goodput.
- D0 reference disaggregated baseline running, or a documented reason it can't.
- KV-size calculator (per model, per layout); message-size profile of real requests.
- `docs/prior_art.md`, covering:
  - DistServe, Splitwise, Mooncake, NIXL/Dynamo, vLLM KV connectors, SGLang PD,
    Sarathi-Serve
  - for each one: its mechanism, its gap, and what kvwire reuses
  - a go/re-scope decision on the fencing and fault-behavior gap

**Exit**
- Ceilings recorded.
- C0 goodput curve for ≥ 2 workloads.
- ADRs 0001–0004 accepted or revised.
- Brief §6 targets revised with data.

`[OWNER-CORE]`: GPUDirect bring-up diagnosis; the prior-art gap analysis.

## M2 — RDMA KV transport (C++)

**Deliverables**
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
- K06 and K07 pass in isolation, with zero corruption.

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

`[OWNER-CORE]`: layer-wise trigger and overlap logic (with Claude reviewing the vLLM
integration).

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
- Crossover heatmap.
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
- Rehearsed interview defense.
- Clean-room check and public-release clearance.

**Exit**
- Every public number links to a run id.
- An outside reviewer can reproduce the ceiling sweep and one D1-vs-D3 TTFT comparison
  from the README.
