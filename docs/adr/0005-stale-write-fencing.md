# ADR-0005: Stale-write fencing mechanism

- Status: Proposed. Decide after the first M2 experiment (MW bind over GPU MRs).
- Deciders: Naresh ([OWNER-CORE]) + Claude Code as advisor

## Context
Transfer T times out; its decode blocks are freed and reassigned to request R; a late WRITE from T
lands in R's KV → silent corruption (TRANSPORT §5, FAULT_MATRIX K07). Invariant (ARCHITECTURE §6):
no write from an older epoch can land in a block after it is reused.

## Options considered
1. **Per-transfer type-2 memory window, invalidated by the receiver before reuse.**
   Pros: receiver-controlled; NIC enforces it (remote access error). Cons: bind WR per transfer;
   GPU-MR support unverified; MW count limits.
2. **Receiver-side QP ERR/RESET on abort** (+ reconnect). Pros: no MW dependency. Cons: collateral
   damage to other transfers sharing the QP; DMA-quiescence guarantee must be verified.
3. **Sender-side QP ERR + lease ≥ retransmit horizon.** Cons: sender may be dead; horizon does
   not bound in-fabric packets; infinite settings (timeout=0, rnr_retry=7). Supplementary only.
4. **Epoch tags validated at commit.** Detection only — always on, never sufficient alone.

## Decision
TBD with data. Record: mechanism, measured bind/reset cost, K07 result (≥ 20 trials, ≥ 2 rails).

## Consequences
TBD.
