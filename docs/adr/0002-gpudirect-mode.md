# ADR-0002: GPUDirect registration path (dmabuf vs nvidia-peermem)

- Status: Proposed. Decide after M1 bring-up.

## Criteria

- Support on the installed kernel, driver, and rdma-core.
- Registration cost.
- Behavior with a large KV pool (BAR1).
- Operational fragility.
- Which path upstream stacks (NIXL/UCX) use by default.

## Also decided here (from ADR-0007)

Whether `cuFlushGPUDirectRDMAWrites` is required when decode is ordered by the host
observing the commit CQE (OQ-5b). Measured in M2.

## Fallback

Host staging, clearly labeled and measured as a separate configuration.
