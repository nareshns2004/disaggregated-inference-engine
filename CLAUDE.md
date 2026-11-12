# kvwire: guidance for AI coding agents

This file is read automatically by Claude Code (and is useful to any coding agent or new
contributor). Human contributors should start with [CONTRIBUTING.md](CONTRIBUTING.md).

## What this repo is

**kvwire** (repository: `disaggregated-inference-engine`) splits LLM serving into prefill
and decode GPU pools and moves the KV cache between them over GPUDirect RDMA. It is **not**
a new inference engine: it plugs a verbs transport, a KV re-layout kernel and a
failure-aware coordinator into vLLM through its KV connector interface (ADR-0001).

The three headline numbers it must earn with measurements:
1. **Transport efficiency**: KV transfer throughput as a % of the measured perftest
   ceiling at realistic paged, per-layer message sizes (both denominators, EVALUATION §1).
2. **TTFT** against a TCP transport, a reference connector and colocated serving,
   including the regime where disaggregation *loses*.
3. **Request success under fault**, with **zero corrupted outputs** as a hard gate.

Sibling project: goodput (fault attribution for multi-node training) shares the
fault-injection discipline and possibly, later, the topology schema and an RDMA transport
library (ADR-0004).

## Maintainers and calibration

The maintainer has a kernel-networking / RDMA / NCCL / GPU-infrastructure background: treat
verbs, PCIe, IOMMU and NIC topics peer to peer; explain vLLM internals, attention and KV
layouts, and scheduler theory when they come up. Optimize for **defensibility over
velocity**: when a choice would not survive a skeptical reviewer, say so.

## Source-of-truth docs: read the relevant one before acting (do not bulk-load)

| Doc | Read when |
|---|---|
| `docs/PROJECT_BRIEF.md` | Scope, priorities, "should we build X", positioning |
| `docs/prior_art.md` | Any claim about what existing systems do or don't cover |
| `docs/ARCHITECTURE.md` | Component boundaries, engine integration, request lifecycle |
| `docs/TRANSPORT.md` | Anything under `transport/`: verbs, MRs, QPs, completion, fencing |
| `docs/FAULT_MATRIX.md` | Failure handling, coordinator, fault injection |
| `docs/EVALUATION.md` | Anything in `bench/`; any number that will be reported |
| `docs/MILESTONES.md` | Start of every session; planning; deciding "done" |
| `docs/OPEN_QUESTIONS.md` | Before writing code that depends on an unresolved decision |
| `docs/ENVIRONMENT.md` | Before any command on real hardware |
| `docs/adr/` | Before re-opening a decided question |

## Operating rules (non-negotiable)

1. **Plan before code.** Every milestone and non-trivial component starts with a plan
   (plan mode; design docs in `docs/design/`): files, interfaces, tests, how the result
   will be measured, open questions. Wait for maintainer approval.
2. **Ownership boundaries.** Components tagged `[OWNER-CORE]` in `docs/MILESTONES.md` are
   implemented by the maintainer. For those, propose interfaces, write tests, fixtures and
   microbenchmarks, and review hard. Do not write the implementation unless the
   maintainer says "you write it" in that session.
3. **No fabricated numbers.** No latency, bandwidth, TTFT, TPOT, goodput or success-rate
   figure anywhere unless it comes from `bench/results/<run_id>/` with an environment
   manifest. Literature numbers are cited and labelled; model-derived numbers (KV-size
   arithmetic) are labelled as calculations. `scripts/check_numbers.py` guards docs.
4. **Perf claims need a ceiling.** Every transport number sits next to the measured
   perftest ceiling (same NIC, message size, QP count, GPU vs host memory). Every kernel
   number sits next to the DRAM-bandwidth roofline.
5. **Correctness is a gate, not a metric.** A change that alters greedy outputs versus the
   reference beyond the documented tolerance is a bug and blocks merging.
6. **Hardware safety.** Act only on allowlisted hosts in `docs/ENVIRONMENT.md`. Never run
   without explicit same-session confirmation: driver/firmware/OFED changes,
   `nvidia-peermem` or IOMMU/ACS/BIOS changes, NIC or switch config (PFC, ECN, MTU, GID),
   reboots, GPU resets, or `rm` outside the repo or `/scratch/kvwire`. Fault injections
   register a revert first and auto-revert on timeout.
7. **Clean-room / IP.** This is a public project. Never introduce code, configs,
   hostnames, IPs, internal tool names, logs or data from any employer or third party. If
   something looks like proprietary material, stop and ask.
8. **Reuse before reinvent.** Use vLLM, perftest, rdma-core, NIXL/UCX (as baselines),
   Nsight and Triton. Novelty lives in small-message transport efficiency, stale-write
   fencing and fault semantics, the gated re-layout kernel, and the evaluation. Any "build
   it ourselves" choice needs an ADR.
9. **Scope discipline.** Must > Should > Stretch (see the brief). Flag scope creep out
   loud. The Triton kernel ships only on a measured net win (ADR-0003).
10. **Tests.**
    - Transport: loopback tests, or SoftRoCE `rxe` for logic-only runs (labelled
      non-performance).
    - Coordinator/scheduler: CPU-only tests with the simulated engine.
    - Kernel: exhaustive shape tests against the PyTorch reference.
    - Hardware tests are marked `gpu` / `multinode` / `rxe`.
11. **Docs move with code.** Interface change → ARCHITECTURE/TRANSPORT in the same change.
    Decision → ADR. Update "Current state" below as milestones progress.

## Commands (keep true; add as they exist)

```
make setup                       # .venv (uv, py3.10) + dev deps + pre-commit
make check                       # lint + typecheck + CPU tests + number guard (Python CI)
make transport                   # CMake build; verbs backend only if libibverbs found
make test-transport              # C++ unit tests
make test-rxe                    # transport logic over SoftRoCE (non-performance)
make test-gpu / test-multinode
make env-manifest                # writes docs/ENVIRONMENT.md generated section
make topo                        # (M1) GPU↔NIC PCIe/NUMA affinity -> artifacts/topology.json
make ceiling                     # perftest sweep -> bench/results/<run_id>/ceiling/
make bench SCENARIO=<path.yaml>  # (M1) serving experiment -> bench/results/<run_id>/
make report RUN=<run_id>         # (M1+)
```

## Code conventions

- C++20 for `transport/`: RAII wrappers for every verbs object; no exceptions across the C
  ABI or pybind boundary (return `Status`); `-Wall -Wextra -Werror -Wpedantic`;
  ASan/UBSan/TSan builds. The hot path does not allocate, lock or log per work request.
- Python ≥ 3.10 with full typing, `ruff`, `mypy --strict` on `kvwire/`, `faultlab/`,
  `bench/`, and `pytest`. `kvwire/transport/base.py` mirrors the C++ headers (a test
  enforces status-code parity).
- Triton kernels live in `kernels/`, each with a PyTorch reference and a benchmark script.
- Cross-process messages use versioned schemas. Durations use monotonic clocks;
  cross-host correlation uses UTC epoch-ns, with clock-sync assumptions documented.
- Commits: conventional commits, DCO sign-off, one logical change each; the message says
  *why*.
- Personal, local-only notes go in `.local/` or `CLAUDE.local.md` (both gitignored).

## Current state

- Milestone: **M1** (baselines, workload/trace harness, hardware ceilings, prior-art gate).
- Open decisions: ADR-0001 to ADR-0005 are *Proposed*; ADR-0006 is *Accepted*. See
  `docs/OPEN_QUESTIONS.md`.
- Implemented: `kvwire/kvcalc`, schemas, transfer state-machine table, in-memory registry,
  env manifest probe, retransmit-horizon arithmetic, faultlab ledger. Everything else is
  interfaces and stubs. No measurements yet.
