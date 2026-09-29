# Architecture — kvwire

Status: initial design. *(ADR)* marks decisions to ratify.

## 1. Design principles

1. **Integrate, don't fork.** The engine is vLLM, pinned. kvwire lives behind vLLM's KV
   connector interface and an external router. Patches to vLLM are a last resort, kept
   minimal and documented.
2. **Control plane and data plane are separate.** The coordinator decides; the transport
   moves bytes. Metadata travels over TCP/gRPC; KV bytes travel over RDMA only.
3. **Hide transfer behind compute.** Transfer is layer-wise and pipelined with prefill.
4. **Every byte has an owner and an epoch.** A KV block is writable by exactly one transfer
   generation at a time. Fencing is designed in, not bolted on (see TRANSPORT §5).
5. **Correctness gates performance.** Greedy outputs must match the reference.

## 2. System context

```
  clients ──► router / coordinator ──(assign P,D; transfer ids; SLO admission)──┐
                │        ▲  health, queue depth, KV occupancy                   │
                ▼        │                                                      ▼
   ┌──── prefill pool (TP=p) ────┐   RDMA WRITE (GPUDirect)    ┌──── decode pool (TP=d) ────┐
   │ vLLM worker + kvwire        │ ═══ layer-wise KV stream ══►│ vLLM worker + kvwire       │
   │ connector (send side)       │   multi-rail, fenced        │ connector (recv side)      │
   │ [re-layout kernel if p≠d]   │                             │ [unpack kernel if needed]  │
   └─────────────────────────────┘                             └────────────────────────────┘
           ▲ faultlab (shared design with goodput): node kill, link flap, QP error, delay
```

## 3. Request lifecycle (happy path)

1. The router admits the request against SLO budgets. It picks a prefill instance P and a
   decode instance D using queue depth, KV occupancy, and topology *(ADR on policy)*.
2. The coordinator asks D to reserve KV blocks. D returns block ids, remote addresses/keys
   (or a memory-window handle), and a transfer epoch.
3. P runs prefill. After each layer's KV is written, the connector enqueues RDMA WRITEs for
   that layer's blocks, packed or SGE-batched.
4. The last write carries an immediate value (or is followed by a flag write) encoding
   (transfer id, epoch, layer count). D's receive path validates the epoch and marks the
   blocks ready.
5. D schedules the request into its decode batch. P frees its KV blocks once the
   transfer's completions are all observed.
6. D streams tokens back through the router.

## 4. Components

### 4.1 Router / coordinator (`kvwire/coordinator/`)
- Holds membership and health for P and D instances (heartbeats plus transport error
  reports).
- Owns the transfer registry: transfer id → (P, D, blocks, epoch, state, deadline).
- Transfer state machine:
  `RESERVED → STREAMING → COMMITTED → DECODING → DONE`, with failure edges to
  `ABORTED` (with fencing), then `RETRY` (on new D, or recompute locally) or `FAILED`
  (fail fast with a clear error). Encoded in `kvwire/coordinator/state_machine.py`.
- Admission control and routing policy (SLO-aware; Should).
- Is not on the data path. A coordinator restart recovers state from instance reports
  *(ADR)*.

### 4.2 Connector (`kvwire/connector/`)
- Adapter from the vLLM KV connector API to the transport. It stays thin; all
  vLLM-version-specific code lives here.
- Send side: hooks the per-layer KV-ready point and enqueues transfers.
- Receive side: allocates/reserves blocks and exposes readiness to the scheduler.

### 4.3 Transport (`transport/`, C++ with pybind11) — see `docs/TRANSPORT.md`
- Device/PD/CQ/QP lifecycle; MR registration of the whole KV pool once per GPU
  (GPUDirect via dmabuf or peermem *(ADR)*); multi-rail GPU↔NIC affinity from topology.
- WR batching, SGE lists, doorbell coalescing, selective signaling, completion polling
  thread per NIC.
- Epoch fencing and stale-write prevention.
- QP error detection and reset/re-create.
- A TCP implementation behind the same interface, as the control experiment.

### 4.4 Kernels (`kernels/`, Triton)
- Pack: gather paged KV blocks for a layer into a contiguous send buffer, with optional
  head re-partitioning when prefill TP ≠ decode TP.
- Unpack: scatter from the receive buffer into the decode side's paged layout.
- Each kernel comes with a PyTorch reference, a shape sweep, and Nsight Compute reports.

### 4.5 Topology (`kvwire/topology/`)
- GPU↔NIC PCIe affinity (`nvidia-smi topo -m`, sysfs), NUMA, and rail mapping. The same
  schema as goodput's `topology.json` so the two repos can share it.

### 4.6 faultlab-lite (`faultlab/`)
- Scenario YAML; mechanisms: process kill (P or D), link down/flap on the RDMA netdev,
  forced QP error (transition the QP to ERR via the transport's test hook), artificial
  receive delay, coordinator kill.
- Ground-truth ledger (the same schema idea as goodput).

### 4.7 bench (`bench/`)
- Load generator: trace-driven (public conversation traces) and synthetic distributions
  (prompt/output length, Poisson/bursty arrivals).
- Per-request timeline capture: arrival, admit, prefill start/end, per-layer transfer
  send/complete, commit, first token, each token, done.
- Report generator.

## 5. Schemas (versioned)

- `TransferDesc {transfer_id, epoch, src{instance, gpu, blocks[]}, dst{instance, gpu,
   blocks[], rkey|mw_handle}, layers, bytes_per_layer, layout{tp, block_size, dtype}}`
- `TransferEvent {transfer_id, epoch, kind(enqueued|layer_sent|committed|aborted|error),
   ts, detail}`
- `RequestTimeline {req_id, ts_* fields, P, D, transfer_id, outcome, tokens_hash}`
- `FaultInjection {id, class, label(real|induced|synthetic), target, t_start, t_end,
   revert_ok}`

## 6. Failure semantics (summary; details in FAULT_MATRIX)

- **D dies before commit:** abort (fence) → pick a new D → re-stream from P's retained KV if
  still held, or recompute prefill.
- **D dies after commit:** the request fails over to a new D with a recompute of prefill
  (the KV is gone). Latency degrades; correctness is preserved.
- **P dies mid-stream:** abort → D releases the reservation → retry prefill on another P.
- **Link flap / QP error:** the transport resets the QP. The in-flight transfer is fenced
  and retried under a new epoch.
- **Coordinator dies:** in-flight transfers complete or time out. A new coordinator
  rebuilds the registry from instance reports.
- **Invariant:** no block is ever readable by decode unless every write of the *current*
  epoch has completed, and no write from an older epoch can land in it afterwards.

## 7. Scaling notes (interview material)

- QP count is roughly (#P GPUs × #D GPUs × rails) with RC. Options: connection pooling,
  lazy connect, DC transport where supported, SRD-style transports on other clouds.
- The coordinator becomes a bottleneck at high QPS. Shard it by request hash; keep the
  per-request state small.
- Prefill:decode ratio depends on workload. The sweep produces a recommendation model;
  online rebalancing is Stretch.

## 8. Repo layout

```
kvwire/        coordinator/ connector/ topology/ schemas/ transport/ (Python facade + TCP)
               kvcalc/ (KV-size calculator) sim/ (simulated engine) cli.py
transport/     include/ src/ tests/ bench/ (C++ microbenchmarks) python/ (pybind)
kernels/       pack.py unpack.py ref.py bench/
faultlab/      scenario.py ledger.py mechanisms/ scenarios/
bench/         scenarios/ loadgen/ report/ results/ (raw gitignored)
scripts/       env_manifest.py ceiling_sweep.sh check_numbers.py
dashboards/
docs/          + design/ prior_art.md REVIEW_NOTES.md adr/
tests/         unit/ integration/ gpu/ multinode/ fixtures/
```
