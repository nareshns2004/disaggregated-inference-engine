# Review notes: scaffold pass (2026-09-29)

Blunt notes from building the skeleton against the bundle docs. Each item should become either a
doc fix, an ADR, or an M1/M2 experiment. Nothing here has been measured. These are design
concerns to verify.

## A. Decisions pending from Naresh

1. **Tracker edit.** Approve the proposal to move the RDMA transport from M4 to M2 and to swap
   fused attention for the gated re-layout kernel in M4 (MILESTONES.md header). If you approve,
   update P2 in the tracker and delete that banner.
2. **ADRs 0001–0004** are *Proposed*. ADR-0005 (fencing) has been added as a stub. It's the
   centrepiece, and it's `[OWNER-CORE]`.
3. **License**, and **public-release clearance** for an area that overlaps the employer POC.
4. **CLAUDE.md is public once pushed.** It names your background and mentions your employer's
   POC. Decide whether to keep it, trim it, or move it to `CLAUDE.local.md` (gitignored).

## B. Technical concerns in TRANSPORT.md / FAULT_MATRIX.md

1. **Fence on the responder, not the requester.** §5 option 2 moves the *sender's* QP to ERR.
   In K01 and K03 the sender may be dead, partitioned or wedged, so the side that owns the
   memory (decode) has to be able to fence on its own. Receiver-side options: invalidate the MW
   (§5 option 1), or move the receiver's own QP to ERR or RESET. Open questions: does
   `ibv_modify_qp(ERR)` returning guarantee no further DMA into host or GPU memory? And if a QP
   is destroyed and re-created, can QPN reuse let a late packet match the new QP? PSN mismatch
   makes that unlikely, but unlikely isn't a guarantee.
2. **The retransmit horizon is weaker than it looks.** `4.096 µs × 2^timeout × (retry_cnt+1)`
   bounds how long the requester keeps retransmitting. It doesn't bound how long a packet that
   was already sent can sit in the fabric (PFC pause storms, deep switch buffers). There are
   more traps: `timeout=0` means infinite, `rnr_retry=7` means infinite, and the HCA can clamp
   the effective timeout upward. Treat lease ≥ horizon as belt-and-braces, never the only fence.
3. **Type-2 memory windows over GPU memory are unverified.** They need the MR registered with
   `IBV_ACCESS_MW_BIND`, and a bind is a WR posted on a QP, so each transfer pays a bind
   latency. Whether MW binding works over dmabuf or peermem MRs on your NIC, firmware and driver
   is the **first M2 experiment**, because it decides ADR-0005. Also check rxe MW support on your
   kernel before relying on it for CI.
4. **WRITE_WITH_IMM consumes a receive WR.** The decode side has to keep an RQ/SRQ replenished,
   or RNR retries kick in, which is another unbounded-delay path (see B2). A flag write avoids
   the RQ but needs polling. Pick one and justify it in ADR-0005.
5. **The KV layout decides the message count.** The 64 KiB-per-block figure assumes K and V are
   adjacent per block. If the pinned vLLM backend keeps K and V in separate tensors, it's 32 KiB
   and twice as many regions (`kvwire kv-size --layout separate`). Pin this down in M1, since it
   changes the SGE/WR budget in §4.
6. **Metric #1's denominator is ambiguous.** "`ib_write_bw` at the equivalent aggregate size"
   could mean the ceiling at the region size (32–64 KiB) or the large-message peak. Report
   against **both**. The headline should use the large-message peak (true line rate). Otherwise
   strategy (a) looks better than it is and (c) gets no credit.
7. **Multi-rail commit.** RC ordering holds only within one QP. The receiver has to count a
   commit per rail and must never infer completeness from a single rail's imm. §5 already says
   this; K07 has to be tested with ≥ 2 rails too.

## C. Scope and methodology

- The crossover (H3) and the "where we lose" section are mandatory. Don't trim them in M6.
- Pin the SLO values *before* running C0, to avoid SLO shopping.
- If only one GPU node is available, the headline TTFT numbers can't be produced honestly.
  Decide early whether to rent two nodes with GPUDirect-capable NICs for M2 and M3, and record
  the provenance.
