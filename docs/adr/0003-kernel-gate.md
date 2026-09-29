# ADR-0003: Triton kernel scope and merge gate

- Status: Proposed

## Decision

The Triton work is a KV pack/unpack and TP re-partition kernel, not fused attention.

## Merge gate

It merges only if it improves the end-to-end TTFT p50 or the transport efficiency by a
statistically significant margin, on a workload in the evaluation grid, against the best
non-kernel strategy (SGE batching). If it doesn't, it stays in `kernels/` as a documented
negative result.
