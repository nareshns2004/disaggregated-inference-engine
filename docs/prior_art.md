# Prior art: what exists, what it covers, what kvwire reuses

Status: **draft (M1)**. For each system: mechanism, KV transport, fault and fencing story
(and whether it is published), measured numbers (cited, labelled as literature values),
the gap relative to kvwire, and what kvwire reuses. Entries marked *to verify* have not yet
been checked against the primary source.

The gap analysis and the go / re-scope decision at the end are `[OWNER-CORE]` (MILESTONES
M1). The key question: **does any system publish stale-write fencing together with
fault-injection results?** If yes, kvwire re-scopes.

---

## Mooncake (FAST '25) and its Transfer Engine

*Checked 2026-11-12 against the Mooncake / TENT design docs.*

- **Mechanism:** KV-centric disaggregated serving for Kimi; the Transfer Engine moves KV
  over RDMA (multi-NIC, topology-aware) and other transports.
- **Fault handling (published as design, not as measured fault results):**
  - On link errors, the failed connection is removed from both sides' endpoint pools and
    re-established on the next transfer; Mooncake Store reroutes to another reachable NIC
    and temporarily avoids RDMA contexts or CQs it has seen fail.
  - The successor design (TENT) marks a failed rail and resubmits on completion-stage
    errors, can fall back across transports (e.g. RDMA to TCP), and surfaces QP/endpoint
    submission failures as `FAILED` without retry.
  - A secondary source (blog, April 2026) reports RDMA endpoints and QPs leaking under
    peer-failure load. *To verify*; relevant to kvwire's K12 leak test.
- **Not found:** any description of preventing a late write from an aborted transfer
  landing in reused KV blocks (stale-write fencing), or a zero-corruption result under
  fault.
- **Literature values (Mooncake IETF 125 slides and arXiv paper, to verify):** about 87 GB/s
  on 4×200 Gb/s RoCE and about 190 GB/s on 8×400 Gb/s for a 40 GB KV transfer; 75% more
  requests served on real traffic.
- **Reuse:** design reference for multi-NIC topology-aware transfer; candidate reference
  connector for D0.

Sources: [Mooncake Transfer Engine design](https://kvcache-ai.github.io/Mooncake/design/transfer-engine.html),
[TENT overview](https://aionw.github.io/design/tent/overview.html),
[TENT failover](https://aionw.github.io/_sources/design/tent/failover.md),
[RDMA QP leak report (secondary)](https://ccs1112.github.io/2026/04/30/mooncake-endpoint-reclaim.html).

## NVIDIA Dynamo + NIXL

*Checked 2026-11-12 against NIXL and Dynamo docs.*

- **Mechanism:** NIXL is the transfer library under Dynamo (and other stacks): VRAM-to-VRAM,
  non-blocking, over UCX, libfabric, and SRD on AWS EFA.
- **Fault handling:** status codes for failed, unposted, in-progress and re-posted
  transfers; troubleshooting guidance for stuck transfers; a documented teardown order
  (transfer handles, then memory, then remote metadata).
- **Not found:** a documented abort/cancel path with a guarantee that no further remote
  write can land after it, or published fault-injection results. One downstream wrapper
  (NeMo RL) deliberately does not release a failed handle while I/O may still be pending,
  because releasing it would be a use-after-free, which is the same hazard class kvwire
  fences against.
- **Reuse:** D0 reference connector baseline.

Sources: [NIXL troubleshooting](https://docs.nvidia.com/nixl/resources/troubleshooting),
[NIXL quick start](https://docs.nvidia.com/nixl/getting-started/quick-start),
[NeMo RL NIXL I/O](https://docs.nvidia.com/nemo/rl/nightly/apidocs/nemo_rl/nemo_rl.data_plane.nixl.nixl_io.html),
[Dynamo KV cache transfer](https://docs.nvidia.com/dynamo/v1.3.0/additional-resources/tensor-rt-llm-details/kv-cache-transfer).

## Other systems

| System | Mechanism | KV transport | Fault / fencing story | Reuse | Status |
|---|---|---|---|---|---|
| DistServe (OSDI '24) | Phase-disaggregated serving optimised for goodput under SLO | Not the focus | — | Goodput-under-SLO per GPU metric | *to verify* |
| Splitwise (ISCA '24) | Phase splitting across heterogeneous hardware | Layer-wise transfer over IB | — | Layer-wise streaming precedent | *to verify* |
| TetriInfer | Disaggregation with prompt chunking and scheduling | — | — | — | *to verify* |
| Sarathi-Serve | Chunked prefill, colocated | None | n/a | C0 baseline | *to verify* |
| vLLM KV connectors | Pluggable connector API (NIXL, Mooncake, LMCache, others); disaggregated prefill still labelled experimental | Pluggable | — | Integration point (ADR-0001) | *to verify at the pinned version* |
| SGLang PD | Prefill/decode disaggregation | Mooncake, NIXL | — | Alternative engine path | *to verify* |
| LMCache | KV cache offload and sharing layer | Multiple backends | — | — | *to verify* |
| llm-d | Kubernetes control plane; pre-allocates decode blocks and pushes KV during prefill | vLLM connector + NIXL | — | Deployment reference | *to verify* |

---

## Gap analysis and gate decision

`[OWNER-CORE]`: to be written by a maintainer once the entries above are verified.

- Does any system publish stale-write fencing + fault-injection results?
- Evidence:
- Decision (go / re-scope), date:
