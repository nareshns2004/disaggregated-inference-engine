# kvwire — Disaggregated LLM inference with RDMA KV-cache transport

> Working name. Rename freely.

## What this repo is

Prefill and decode have opposite resource profiles (prefill is compute-bound, decode is
memory-bandwidth-bound), and running them on the same GPUs makes them interfere. This repo
splits them into separate GPU pools and moves the KV cache between pools over RDMA
(GPUDirect). It is **not** a new inference engine: it plugs a custom transport, a KV
re-layout kernel, and a failure-aware coordinator into an existing engine (vLLM by default,
see ADR-0001).

The three headline numbers this repo must prove with measurements:
1. **Transport efficiency**: KV transfer throughput as a % of measured line rate
   (`ib_write_bw`) at realistic, paged, per-layer message sizes.
2. **TTFT vs a TCP transport baseline** (and vs colocated serving), including the regime
   where disaggregation *loses*.
3. **Request success rate under fault**: prefill/decode node loss, link flap mid-transfer,
   QP errors, with zero corrupted outputs.

It is the "efficiency at scale" half of a two-project portfolio. The sibling repo (goodput,
a fault-tolerant training orchestrator) is "reliability at scale". Both share a
fault-injection mindset, and possibly a topology discovery module and an RDMA transport
library later (Stretch; see ADR-0004).

## Who you are working with

Naresh is a senior systems engineer with ~9 years across kernel networking, RDMA/RoCE,
DPDK, SR-IOV, KVM, NCCL and GPU infrastructure. Treat him as a peer on verbs, PCIe, IOMMU
and NIC topics; explain vLLM internals, attention/KV layouts and scheduler theory when they
come up. AI-lab and FAANG interviewers will grill him on every line of this repo, so
optimize for **defensibility over velocity**. Whenever a choice would not survive an
interview, say so.

## Source-of-truth docs — read the relevant one before acting (do not bulk-load)

| Doc | Read when |
|---|---|
| `docs/PROJECT_BRIEF.md` | Scope, priorities, "should we build X", positioning |
| `docs/ARCHITECTURE.md` | Component boundaries, engine integration, request lifecycle |
| `docs/TRANSPORT.md` | Anything under `transport/` — verbs, MRs, QPs, completion, fencing |
| `docs/FAULT_MATRIX.md` | Failure handling, coordinator, fault injection |
| `docs/EVALUATION.md` | Anything in `bench/`; any number that will be reported |
| `docs/MILESTONES.md` | Start of every session; planning; deciding "done" |
| `docs/INTERVIEW_DEFENSE.md` | After finishing a component; `/drill` |
| `docs/ENVIRONMENT.md` | Before any command on real hardware |
| `docs/adr/` | Before re-opening a decided question |
| `docs/REVIEW_NOTES.md` | Open technical concerns and pending decisions |

## Operating rules (non-negotiable)

1. **Plan before code.** Every milestone and every non-trivial component starts with a
   plan in plan mode: files, interfaces, tests, how the result will be measured, and open
   questions. Wait for approval.
2. **Ownership boundaries.** Components tagged `[OWNER-CORE]` in `docs/MILESTONES.md` are
   written by Naresh. For those, you propose interfaces, write tests, fixtures and
   microbenchmarks, and review his implementation hard. Do not write the implementation
   unless he says "you write it" in that session.
3. **No fabricated numbers.** No latency, bandwidth, TTFT, TPOT, goodput or success-rate
   figure may appear anywhere unless it comes from `bench/results/<run_id>/` with an
   environment manifest. Literature numbers are cited and labeled; model-derived numbers
   (e.g. KV-size arithmetic) are labeled as calculations.
4. **Perf claims need a ceiling.** Every transport number is reported next to the measured
   hardware ceiling (`ib_write_bw` / `ib_write_lat` from perftest, same NIC, same message
   size, same GPU-memory vs host-memory mode). Every kernel number is reported next to the
   roofline or `cudaMemcpy`/DRAM-bandwidth ceiling.
5. **Correctness is a gate, not a metric.** A change that alters generated tokens under
   greedy decoding versus the reference (beyond the documented numerics tolerance) is a
   bug. It blocks merging, whatever the speedup.
6. **Hardware safety.** Act only on allowlisted hosts in `docs/ENVIRONMENT.md`. Never run
   any of the following without explicit same-session confirmation: driver/firmware/OFED
   changes, `nvidia-peermem` or IOMMU/ACS/BIOS changes, NIC or switch config changes (PFC,
   ECN, MTU, GID), reboots, GPU resets, or `rm` outside the repo or `/scratch/kvwire`.
   Fault injections register a revert first and auto-revert on timeout.
7. **Clean-room / IP.** This is a personal public project. Never introduce code, configs,
   hostnames, IPs, internal tool names, logs or data from Naresh's employer or its internal
   POC. If something looks like employer material, stop and ask.
8. **Reuse before reinvent.** Use vLLM, perftest, rdma-core, NIXL/UCX (as baselines),
   Nsight, and Triton. Novelty lives in the transport's small-message and fault semantics,
   the re-layout kernel, the failure-aware coordinator, and the evaluation. Any "build it
   ourselves" choice needs an ADR.
9. **Scope discipline.** Must > Should > Stretch (see the brief). Flag scope creep out loud.
   The Triton kernel ships only if it measurably improves TTFT or transport efficiency
   (ADR-0003).
10. **Tests.**
    - Transport: loopback tests (same host, two HCAs or one HCA with two ports, or SoftRoCE
      `rxe` for logic-only CI; label rxe results as non-performance).
    - Coordinator/scheduler: CPU-only tests with a simulated engine.
    - Kernel: exhaustive shape tests against a PyTorch reference.
    - GPU and multinode tests are marked `@pytest.mark.gpu` / `@pytest.mark.multinode`.
11. **Docs move with code.** An interface change updates ARCHITECTURE/TRANSPORT in the same
    change. A decision gets an ADR. Update "Current state" below as milestones progress.

## Commands (keep true; add as they exist)

```
make setup                       # python env, C++ build (CMake + pybind11), pre-commit
make test                        # CPU tests (gpu/multinode/rxe auto-skipped)
make transport                   # CMake build; verbs backend only if libibverbs found
make test-rxe                    # transport logic over SoftRoCE (non-performance)
make test-gpu / test-multinode
make env-manifest                # writes docs/ENVIRONMENT.md generated section
make topo                        # GPU↔NIC PCIe/NUMA affinity -> artifacts/topology.json
make ceiling                     # perftest sweep -> bench/results/<run_id>/ceiling/
make bench SCENARIO=<path.yaml>  # serving experiment -> bench/results/<run_id>/
make report RUN=<run_id>
```

## Code conventions

- C++20 for `transport/`: RAII wrappers for every verbs object; no exceptions across the C
  ABI or pybind boundary (return status); `-Wall -Wextra -Werror`; ASan/UBSan/TSan builds.
  The hot path does not allocate, lock, or log per work request.
- Python ≥3.10 (the dev laptop runs 3.10) with full typing, `ruff`, `mypy --strict` on `kvwire/`, and `pytest`.
- Triton kernels live in `kernels/`, each with a PyTorch reference implementation and a
  benchmark script.
- Cross-process messages use versioned schemas. Durations use monotonic clocks;
  cross-host correlation uses UTC epoch-ns, with clock-sync assumptions documented.
- Commits use conventional commits, one logical change each; the message says *why*.

## Current state

- Milestone: **M1** (baselines, workload/trace harness, hardware ceilings, prior-art gate).
- Open decisions: ADR-0001 to ADR-0005 are *Proposed*. See docs/REVIEW_NOTES.md §A.
- Scaffold in place: interfaces + stubs; implemented so far: kvwire/kvcalc, schemas,
  state-machine table, in-memory registry, env manifest probe, retransmit-horizon arithmetic.
