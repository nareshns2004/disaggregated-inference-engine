# Evaluation — kvwire

## 1. Metric definitions (canonical)

- **TTFT:** request arrival at the router → first token emitted to the client.
  Decomposed into:
  - router queue
  - prefill queue
  - prefill compute
  - exposed transfer (transfer time not overlapped with prefill)
  - decode queue
  - first decode step
- **TPOT / ITL:** mean and p99 inter-token latency per request, excluding the first token.
- **E2E latency:** arrival → last token.
- **SLO attainment:** the fraction of requests meeting *both* the TTFT SLO and the TPOT SLO.
  SLO values are chosen per model and stated in the report. A sweep over SLO tightness is
  shown.
- **Goodput:** the maximum arrival rate (req/s) at which SLO attainment is ≥ 90%. It is
  also reported per GPU (DistServe's framing), since disaggregation changes GPU counts.
- **Transport efficiency:** achieved KV bytes/s ÷ perftest `ib_write_bw` (GPU memory,
  same NIC, same effective message size, same QP count) × 100%.
- **Exposed transfer fraction:** exposed transfer ÷ TTFT.
- **Request success rate:** completed requests ÷ admitted requests during a fault run.
  Fast, explicit failures are counted separately from timeouts.
- **Corruption count:** requests whose greedy output differs from the reference beyond
  the numerics tolerance. The target is 0. Any nonzero count blocks the release.
- **Recovery time:** fault → affected requests resume producing tokens (p50/p99).
- **CPU cost:** transport thread CPU-seconds per GB moved.

## 2. Baselines

- **C0:** vLLM colocated, chunked prefill **on**, tuned (the strongest baseline, and the
  one that makes the crossover honest).
- **C1:** vLLM colocated, chunked prefill off. Included for context only.
- **D0:** vLLM disaggregated with a reference connector (NIXL, or whatever vLLM ships as
  default at the pinned version) on the same hardware.
- **D1:** kvwire with the TCP transport.
- **D2:** kvwire with the RDMA transport, naive per-block WRITE (the ablation).
- **D3:** kvwire with the full RDMA transport.

GPU budget parity: C* uses N GPUs; D* uses the same N GPUs split into P and D pools. The
P:D ratio is swept, and the best ratio is reported per workload. State this explicitly.

## 3. Workloads

- **Models:** an 8B-class model for iteration (TP1). A 70B-class model for headline
  results (TP4–8), if the hardware allows.
- **Length distributions:**
  - public conversation traces
  - synthetic grids: prompt ∈ {512, 2K, 8K, 32K}, output ∈ {64, 256, 1K}
  - a long-context RAG-like profile (long prompt, short output), where disaggregation
    should win
  - a chat-like profile (short prompt, long output), where it may not
- **Arrivals:** Poisson at swept rates, plus bursty (gamma with high CV).
- **Heterogeneous TP** (prefill TP ≠ decode TP) for the kernel experiments.

## 4. Protocol

- **Microbenchmarks (transport):**
  - message sizes 4 KiB–64 MiB
  - per-layer block batches at realistic block sizes
  - 1–N QPs, 1–N rails
  - each strategy from TRANSPORT §4
  - ≥ 10 repetitions after warmup; p50/p99 and 95% CI
- **Serving:**
  - each (workload, rate, system) point runs ≥ 10 minutes steady state after warmup
  - ≥ 3 repetitions with interleaved order
  - bootstrap CIs on percentiles
  - the goodput search uses binary search on rate, with a stated termination tolerance
- **Faults:**
  - ≥ 20 trials per Must fault class
  - injection time randomized, with a fixed seed
  - one long mixed-fault run (≥ 2 h) at a stated fault rate and load
  - identical schedules for D0 and D3
- **Correctness:**
  - greedy decoding with fixed seeds
  - the reference is the C0 output on the same model and weights
  - cross-TP numerics differences are measured first, to set the tolerance (logprob
    delta), and documented
  - every fault run is checked
- **Kernel:**
  - Nsight Compute: achieved DRAM bandwidth vs peak, occupancy
  - Nsight Systems timeline showing overlap of pack, WRITE, and prefill
  - net TTFT effect measured end to end (the ADR-0003 gate)

## 5. Reporting standard

- `bench/results/<run_id>/` holds:
  - config
  - environment manifest: GPU, driver, CUDA, vLLM commit, Triton, NIC model and
    firmware, rdma-core/OFED, kernel, GPUDirect mode, PCIe topology hash, NCCL/UCX/NIXL
    versions
  - raw request timelines, transport stats, and the ceiling sweep used for normalization
- Reports are script-generated. No hand-typed numbers.
- **Required plots:**
  - transport efficiency vs message size, one line per strategy, with the ceiling line
  - TTFT decomposition stacked bars (TCP vs RDMA vs reference)
  - SLO attainment vs rate curves
  - a goodput-per-GPU crossover heatmap over prompt × output length (C0 vs D3)
  - success rate and recovery-time CDF under faults
  - Nsight timeline screenshots
- Every README and blog claim links to a run id.
