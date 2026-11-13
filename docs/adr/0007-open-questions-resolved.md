# ADR-0007: Open questions resolved without hardware, and the HF Project 2 contract

- Status: Accepted
- Date: 2026-11-13
- Deciders: maintainers
- Resolves: OQ-2 (partly), OQ-5 (commit signal), OQ-6, OQ-7, OQ-8, OQ-9

## Context
`docs/OPEN_QUESTIONS.md` mixed three kinds of item: decisions that need no hardware,
decisions that only an M1/M2 experiment can settle, and items only the maintainer can
close (hardware, clearance). This ADR settles the first kind so the M1 and M2 plans can be
written. The experiments stay open on purpose, and their ADRs stay Proposed: an ADR that
claims a hardware result before the run would break rule 3.

It also records how this repo feeds **Hugging Face Project 2**. The portfolio has exactly
two GitHub repos (goodput = GitHub Project 1, reliability; kvwire = GitHub Project 2,
efficiency) and exactly one HF model and one HF dataset in total. The dataset slot is
kvwire's.

## Decisions

| Item | Decision |
|---|---|
| OQ-2 | **Accepted now:** ADR-0001 (vLLM KV connector; exact version and attention backend pinned at M1 bring-up), ADR-0003 (re-layout kernel scope and merge gate), ADR-0004 (sharing rules, amended below). **Stay Proposed until their experiment:** ADR-0002 (GPUDirect mode, M1 bring-up) and ADR-0005 (fence mechanism, first M2 experiment: MW bind over GPU MRs; otherwise receiver-side QP ERR/RESET with its collateral cost measured). |
| OQ-5 (commit) | Commit = **WRITE_WITH_IMM per rail**, received on an **SRQ kept replenished** (low-water refill + `IBV_EVENT_SRQ_LIMIT_REACHED` alarm), with **`rnr_retry ≤ 6`**, never 7. The RNR budget is now part of the horizon (`RnrHorizon`, `FenceHorizon` in `transport/src/horizon.cc`). Flag-write commit rejected: it needs polling and gives decode no CQE to order on. The remaining part of OQ-5 (whether `cuFlushGPUDirectRDMAWrites` is needed when decode is ordered by the host observing the CQE) is a GPU-visibility question, so it moves to ADR-0002 and is measured in M2. |
| OQ-6 | The pinned backend's K/V layout is an **M1 deliverable** (`kvwire kv-size --layout` against the pinned vLLM), recorded in ADR-0001 when pinned. Until then every grid covers **both** layouts, so no result depends on the guess. |
| OQ-7 | The M2 microbenchmark grid explicitly includes **16, 32 and 64 KiB** regions, the **separate-K/V** layout, and a **decode TP = 2 head split** (which halves region size). H1 is tested where the M1 efficiency-vs-size curve shows a gap; if there is no gap anywhere in that grid, H1 is reported as refuted. |
| OQ-8 | Public name **kvwire** everywhere: the repository is renamed from `disaggregated-inference-engine` to `kvwire` (GitHub redirects the old URL). The PyPI name `kvwire` was free when checked. |
| OQ-9 | No shared `topology.json` is claimed. kvwire's per-host GPU↔NIC link matrix is a natural *host detail* of goodput's hosts-plus-placement model; converge only when both repos have a topology file produced on real hardware. ADR-0004 is amended to say so. |

Still open (not decidable without hardware or the maintainer): OQ-1 (target hardware),
OQ-3 (MW bind over GPU MRs), OQ-4 (receiver-side QP reset guarantees), OQ-10
(publication clearance).

## Hugging Face Project 2 contract

| Artifact | Built from | Rule |
|---|---|---|
| `nareshns2004/rdma-kv-transfer-traces` (HF dataset, CC-BY-4.0) | `kvwire export` over `bench/results/<run_id>/` | Six configs: `transfers`, `transfers_raw`, `layer_timelines`, `ceilings`, `prefill`, `environments`. No row without a same-config ceiling; `rxe` rows never enter it; host-staging rows labelled. Each version is tied to a kvwire commit. |
| `nareshns2004/disagg-kv-explorer` (HF Space) | The dataset only | Efficiency, transfer vs recompute, break-even and exposed-transfer views over measured rows; interpolation drawn dashed, extrapolation refused, no serving simulation, no TTFT/SLO numbers. |

The dataset can ship **v0 with only `ceilings` and `environments`** as soon as the M1
perftest sweep runs: the earliest real public artifact in the portfolio. Nothing is
uploaded without a passing `kvwire export --validate` and cleared hardware (OQ-10).
Export code is CPU-only with optional extras (`pyarrow` for Parquet, `huggingface_hub` for
`--push`), keeping the core dependency-free.

## Options considered (abbreviated)
- Commit signal: flag write + polling (no RQ, but burns a core and has no completion to
  order on); WRITE_WITH_IMM with `rnr_retry = 7` (simplest, but an unbounded wait inside
  the fence horizon). Rejected.
- OQ-2: accept every ADR now (would claim GPUDirect and MW results that do not exist).
  Rejected.
- OQ-9: force one topology schema now (couples two Must paths across repos, against
  ADR-0004's rule). Rejected.

## Consequences
- TRANSPORT §5, EVALUATION, MILESTONES, ADR-0001/0003/0004, README and CLAUDE.md are
  updated in the same change.
- Revisit the commit decision if SRQ refill cannot keep up at the target request rate in
  M2 (measure RNR NAK counters, `rnr_nak_retry_err`).
