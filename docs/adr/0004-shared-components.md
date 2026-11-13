# ADR-0004: Sharing with the goodput repo

- Status: Accepted (2026-11-13, ADR-0007)

## Candidates

- **Topology schema.** Not shared yet (ADR-0007): converge only when both repos have a
  topology file produced on real hardware. kvwire's
  `kvwire/topology/schema.py` (per-host GPU↔NIC link matrix) and goodput's
  `goodput/schemas/topology.py` (hosts + rank placement + failure domains) differ, so docs
  must not claim a shared `topology.json` until one schema is adopted by both.
- **faultlab ledger schema.** Share the design; keep separate implementations.
- **RDMA transport library.** Share only after M2 stabilizes here; goodput's checkpoint
  replication is a Stretch consumer.

## Rule

No cross-repo dependency may block a Must milestone in either repo.
