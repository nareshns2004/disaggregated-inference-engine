# Open questions

Design concerns and pending decisions, first collected in the scaffold review (2026-09-29;
updated 2026-11-13). Nothing here has been measured. Each item becomes a doc fix, an ADR or
an experiment; once resolved, it moves to the table at the end with a link to where it was
settled.

## Blockers

**OQ-1 · Target hardware.** Headline numbers 1–3 need two GPU nodes with GPUDirect-capable
RDMA NICs. Record `nvidia-smi topo -m`, `ibv_devinfo` and provenance/clearance in
`docs/ENVIRONMENT.md` before M2. With one node only, the TTFT results cannot be produced
honestly; decide early whether to rent two nodes.

## Transport and fencing (decided by M2 experiments)

**OQ-3 · Type-2 memory windows over GPU memory are unverified.** They need MRs registered
with `IBV_ACCESS_MW_BIND`, and each bind is a WR on a QP, so every transfer pays a bind
latency. Whether MW bind works over dmabuf or peermem MRs on the target NIC, firmware and
driver is the **first M2 experiment** and decides ADR-0005. Also check SoftRoCE MW support
before relying on it for logic tests.

**OQ-4 · Receiver-side QP reset guarantees.** Does `ibv_modify_qp(ERR)` returning guarantee
no further DMA into host or GPU memory? After destroy and re-create, can QPN reuse let a late
packet match the new QP? PSN mismatch makes it unlikely, but unlikely is not a guarantee.
Needed if ADR-0005 falls back to option 2.

**OQ-5b · GPU visibility of the committed data.** The commit signal is decided
(WRITE_WITH_IMM per rail, ADR-0007). Still open: whether `cuFlushGPUDirectRDMAWrites` is
needed when decode is ordered by the host observing the CQE. Measured in M2; recorded in
ADR-0002.

## Publication

**OQ-10 · Publication clearance.** Written clearance for any hardware used to produce
published numbers, recorded in `docs/ENVIRONMENT.md` → Provenance.

## Resolved

| Item | Resolution | Where |
|---|---|---|
| Milestone order (transport in M2; re-layout kernel instead of fused attention in M4) | Adopted; rationale kept in the milestone doc | MILESTONES |
| Licence | Apache-2.0 (LICENSE, pyproject, README) | LICENSE |
| Agent instructions file is public | Rewritten without personal or employer details; local notes go in gitignored `CLAUDE.local.md` / `.local/` | CLAUDE.md |
| Fence on the responder, not the requester | Sender-side QP reset + lease demoted to supplementary; C++ `FenceMechanism` aligned | TRANSPORT §5, ADR-0005, `fence.h` |
| Retransmit horizon weaker than it looks | Formula fixed to (retry_cnt + 1) attempts; traps documented (timeout = 0, HCA clamp, RNR, in-fabric packets) | TRANSPORT §5, FAULT_MATRIX |
| Ambiguous denominator for metric #1 | Report both; headline uses the large-message peak | EVALUATION §1, PROJECT_BRIEF §6 |
| Multi-rail commit counting | Per-rail commits required; K07 runs with ≥ 2 rails | TRANSPORT §5, FAULT_MATRIX, EVALUATION §4 |
| R vs I labels on scheduled faults | R only for unscheduled failures | ADR-0006, FAULT_MATRIX |
| SLO shopping | SLOs pinned before C0 runs | EVALUATION §4, MILESTONES M1 |
| Crossover could be trimmed | "Where disaggregation loses" is an M5/M6 exit criterion | MILESTONES |
| OQ-2 (partly), OQ-5 commit signal, OQ-6 KV layout, OQ-7 H1 regime, OQ-8 public name, OQ-9 topology convergence | ADR-0001/0003/0004 accepted (0002, 0005 wait for experiments); WRITE_WITH_IMM + SRQ + `rnr_retry ≤ 6` with the RNR term in the horizon; layout pinned in M1 with both layouts in every grid; 16/32/64 KiB, separate-K/V and TP=2 in the M2 grid; repo renamed `kvwire-disaggregated-inference-engine`; no shared topology file claimed | [ADR-0007](adr/0007-open-questions-resolved.md) |
| Python/C++ status codes drifted | Python enum completed; parity test added | `tests/unit/test_transport_parity.py` |
