# transport/ — C++20 verbs KV transport

Design: [`docs/TRANSPORT.md`](../docs/TRANSPORT.md). Fencing decision: ADR-0005.

```
include/kvwire/transport/
  status.h     Status codes (no exceptions across ABI/pybind)
  types.h      Region, LayerBatch, RemoteGrant (mirrors kvwire/schemas)
  strategy.h   small-message strategies (a)-(d)
  device.h     RAII Device / PD / CQ, async event thread
  mr.h         whole-pool MR (host / dmabuf / peermem)
  qp.h         RC QP state machine, PostLayer hot path, Reset
  fence.h      stale-write fencing + retransmit-horizon arithmetic
  transport.h  backend-neutral interface (RDMA and TCP)
```

Builds on a laptop without rdma-core (TCP + interfaces only). The verbs backend is added
automatically when `libibverbs` is found. Hot-path rules: no allocation, locking, or logging per WR.
