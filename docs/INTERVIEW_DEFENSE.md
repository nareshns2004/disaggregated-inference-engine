# Interview Defense — kvwire

Use this with `/drill`. Every answer must point to an artifact in this repo: a file, a
run id, or a plot.

## Framing

1. Why disaggregate at all? When is it a bad idea?
   A strong answer covers: the interference mechanism; chunked prefill as the
   counter-argument; the crossover heatmap.
2. Why not just use NIXL, Mooncake, or Dynamo?
   Cover: `prior_art.md`, the measured delta, and where kvwire lost.
3. What's goodput, and why is it the right metric rather than throughput?
   Cover: SLO attainment and per-GPU normalization.

## KV cache and data movement

4. How big is the KV cache for your model at 8K tokens? Derive it.
   Cover: layers × kv_heads × head_dim × 2 × dtype bytes; the effect of GQA.
5. Why are paged per-layer messages hard for RDMA?
   Cover: WR rate limits, doorbells, SGE limits, and the efficiency-vs-size curve.
6. Walk me through a layer's KV from prefill HBM to decode HBM.
   Cover: the PCIe path, the GPU↔NIC affinity, and why PIX is preferable to SYS.
7. dmabuf vs peermem — what's the difference, and what did you choose?
8. What breaks GPUDirect RDMA on a real server?
   Cover: ACS/IOMMU, BAR1, and topology.
9. How does decode know the KV is complete and visible?
   Cover: write-with-immediate, RC ordering, multi-rail commit counting, and GPU
   visibility/flush semantics.
10. How did you hide transfer time?
    Cover: layer-wise overlap, the Nsight timeline, and the exposed-transfer fraction.
11. Why not NCCL send/recv for KV transfer?
    Cover: communicator semantics, dynamic peer sets, and failure behavior.
12. Why not host staging? Quantify it.
    Cover: the fallback measurement.

## Correctness and failure

13. Describe the stale-write bug and how you made it impossible.
    Cover: memory windows or QP reset plus the retransmit horizon; the K07 result.
14. A decode node dies after commit. What does the user see, and how long does it take?
15. How do you know no request got corrupted KV?
    Cover: the greedy-match gate, how the tolerance was derived, and the zero count
    across runs.
16. QP goes to ERR. Walk me through recovery.
17. How do you avoid KV memory leaks on abort paths?

## Scheduling and scale

18. How do you choose the P:D ratio, and what happens when the workload shifts?
19. SLO-aware admission: what do you reject, and when?
20. Scale to 1,000 GPUs: QP count explosion, coordinator bottleneck, connection setup
    cost.
21. How would this change for MoE, speculative decoding, or long-context (128K+)?

## Kernel

22. Why a re-layout kernel instead of a fused-attention kernel?
23. How close is it to the roofline, and what limits it?
24. Did it earn its place? Show the net TTFT effect.

## Methodology

25. How did you make sure C0 wasn't a strawman?
    Cover: chunked prefill, tuning, and GPU parity.
26. How many repetitions, which CIs, and how did you search for goodput?
27. Which results would change on a different NIC or fabric?

## Honest limitations (say these before being asked)

- The scale that was actually run.
- Which faults were induced vs real.
- Where D0 or C0 won.
- Recompute on failover after commit (no KV replication).
