# ADR-0004: Sharing with the goodput repo

- Status: Proposed

## Candidates

- **Topology schema.** Share; this is cheap. *Status (2026-11-12):* not yet shared. kvwire's
  `kvwire/topology/schema.py` (per-host GPU↔NIC link matrix) and goodput's
  `goodput/schemas/topology.py` (hosts + rank placement + failure domains) differ, so docs
  must not claim a shared `topology.json` until one schema is adopted by both.
- **faultlab ledger schema.** Share the design; keep separate implementations.
- **RDMA transport library.** Share only after M2 stabilizes here; goodput's checkpoint
  replication is a Stretch consumer.

## Rule

No cross-repo dependency may block a Must milestone in either repo.
