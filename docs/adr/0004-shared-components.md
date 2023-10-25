# ADR-0004: Sharing with the goodput repo

- Status: Proposed

## Candidates

- **Topology schema.** Share now; this is cheap.
- **faultlab ledger schema.** Share the design; keep separate implementations.
- **RDMA transport library.** Share only after M2 stabilizes here; goodput's checkpoint
  replication is a Stretch consumer.

## Rule

No cross-repo dependency may block a Must milestone in either repo.
