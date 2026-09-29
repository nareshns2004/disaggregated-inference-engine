# Transport design — kvwire

This is the moat. Every choice here must be explainable from first principles by Naresh.

## 1. Requirements

- GPU memory to GPU memory across nodes, without host staging (GPUDirect RDMA).
- Many small, scattered, per-layer messages at near line rate.
- Layer-wise streaming, overlapped with prefill compute.
- Completion notification to the receiver, with exactly-once semantics per epoch.
- Survives QP errors, link flaps, and peer death without corrupting any request.
- Low CPU cost; no per-WR allocation, locking, or logging on the hot path.

## 2. Bring-up checklist (M1, recorded in ENVIRONMENT)

- `nvidia-smi topo -m`: each GPU's nearest NIC (PIX/PXB preferred over NODE/SYS).
- GPUDirect path: dmabuf (`ibv_reg_dmabuf_mr`) vs `nvidia-peermem`. Check kernel, driver,
  and rdma-core support *(ADR-0002)*.
- ACS/IOMMU settings on the PCIe switches between GPU and NIC; how they affect P2P.
- BAR1 size vs the KV pool size you intend to register.
- `ib_write_bw` / `ib_write_lat` with `--use_cuda`, swept over message sizes and QP counts:
  this is the ceiling every transport number is reported against.

## 3. Memory registration

- Register each GPU's entire KV pool once at startup. Never register per request (MR
  registration is expensive, and it pins/maps pages).
- The receive side publishes (addr, rkey) per pool, or per-transfer memory windows (see §5).
- Registration cost and the MR-count limits of your NIC are measured and recorded.

## 4. Data movement

- **Unit of work:** (layer, set of blocks). For each layer, WRITEs are posted for its
  blocks once prefill has produced that layer's KV. The CUDA event for the layer is the
  trigger. How the CPU learns the event completed (polling thread vs stream callback)
  is a latency trade-off to measure.
- **Small-message strategy.** Options, compared in the M2 microbenchmark:
  a. One WRITE per block per layer (baseline, expected to fall short of line rate).
  b. SGE lists: several source blocks → one contiguous remote region (bounded by
     `max_sge`).
  c. Pack kernel into a contiguous staging buffer on the GPU → one large WRITE per layer
     (kernel cost vs WR savings).
  d. WR chaining with doorbell coalescing and selective signaling (signal every Nth WR).
- **Multi-rail.** Stripe layers or blocks across NICs, respecting GPU↔NIC affinity.
  Measure whether cross-PCIe-switch rails help or hurt.
- **Queue depth and outstanding WRs.** Tune against the CQ size and the NIC's limits;
  document the chosen values and why.
- **Layout mismatch.** When prefill and decode TP or block size differ, either (c) with
  re-partitioning in the pack kernel, or receive-side unpack. Choose by measurement.

## 5. Completion, ordering, and fencing

- **Completion signal.** A final RDMA WRITE-with-immediate carrying (transfer id, epoch),
  or a flag write after the data. Rely on RC in-order delivery on a single QP. With
  multiple QPs/rails, the receiver must count per-rail commits.
- **GPU visibility.** Data written by the NIC into GPU memory must be visible to the decode
  kernels that read it. Understand the GPUDirect RDMA consistency model, and when an
  explicit flush (e.g. `cuFlushGPUDirectRDMAWrites`) is required. This depends on whether
  the consumer is ordered via the host observing completion or via GPU-side flag
  polling. Verify against NVIDIA docs for your CUDA version.
- **Stale-write hazard.** If transfer T times out and its blocks are freed and reassigned
  to request R, a delayed WRITE from T can land in R's KV. The result is silent
  corruption. Mitigations to evaluate *(ADR-0005 when decided)*:
  1. Invalidate access before reuse. Per-transfer type-2 memory windows bound to the
     blocks, invalidated on abort. The NIC then rejects late writes with a remote access
     error.
  2. Move the sender's QP to ERR/reset on abort, and wait for flush completions before
     freeing on the receive side. This needs a round trip, or a lease timeout ≥ the
     maximum retransmit horizon (computed from the IB timeout × retry count).
  3. Epoch-tagged blocks, validated by the receiver before readiness. This detects the
     problem but does not prevent the overwrite. Insufficient alone; combine it with 1
     or 2.
- **Idempotency.** A retransmitted commit for an already-committed or aborted epoch is
  ignored.

## 6. Error handling

- CQ error completions (retry exceeded, remote access error, flush) → the QP moves to
  ERR → the transport drains, resets the QP (RESET→INIT→RTR→RTS) or re-creates it,
  reports to the coordinator, and fences affected transfers.
- Port state events via async events (`ibv_get_async_event`) → fast link-down detection,
  without waiting for retry exhaustion.
- Every error path has a test. Use rxe or a test hook for logic; use real faults for timing.

## 7. TCP control variant

The same interface, over sockets, with the same layer-wise streaming. It exists to show
what RDMA buys, not as a strawman. Tune it reasonably (large buffers, multiple
connections, zero-copy where available) and document the tuning.

## 8. What gets measured (feeds EVALUATION)

For each strategy in §4, versus message size, QP count, and rails:
- Throughput as % of the ceiling.
- Latency p50/p99.
- CPU cycles per GB.
- WRs per second.
- Exposed transfer inside TTFT.
