# Fault Matrix — kvwire

**Labels:** R = real, I = induced (real mechanism, triggered on purpose), S = synthetic.

**Invariant under every fault:** no request returns tokens computed from wrong KV. A
request that cannot be served correctly fails fast with a clear error. It never
returns garbage.

Before trusting any mechanism or default below, verify it for your driver, rdma-core, and
vLLM versions.

| ID | Fault | Phase | Injection | Label | Detection | Required behavior | Tier |
|---|---|---|---|---|---|---|---|
| K01 | Decode instance dies before commit | Streaming | SIGKILL D worker | R | Heartbeat loss; sender CQ errors (retry exceeded) | Fence → new D → re-stream from P's retained KV, else recompute | Must |
| K02 | Decode instance dies after commit | Decoding | SIGKILL D mid-generation | R | Heartbeat loss; token stream stalls | Fail over to new D with prefill recompute; partial tokens are handled per ADR (restart the stream or resume) | Must |
| K03 | Prefill instance dies mid-stream | Streaming | SIGKILL P | R | Heartbeat loss; receiver commit timeout | Abort; D frees the reservation; retry on another P | Must |
| K04 | RDMA link down during transfer | Streaming | `ip link set <netdev> down` / `ibportstate` disable | R | Async port event; CQ errors | Fence; retry on another rail or D; QP recovery once the link returns | Must |
| K05 | Link flapping | Any | Repeated down/up with jitter | R | Port events; error counters | Rail marked unhealthy after N flaps per window; traffic moved off it | Must |
| K06 | QP enters ERR (no physical fault) | Streaming | Transport test hook forces ERR / bad rkey | I | Error completion | QP reset/recreate; transfer fenced and retried; no leak | Must |
| K07 | Delayed / late write after abort | Streaming | Hold WRs (test hook or congestion), abort the transfer, reuse the blocks | I | Must be *prevented*: remote access error on the late write | Zero corruption; the block reused by another request is intact | Must |
| K08 | Receiver slow (decode overloaded) | Commit | Artificial delay in the receive path | I | Commit latency; queue depth | Backpressure to the router; no unbounded buffering | Must |
| K09 | Fabric congestion | Streaming | Competing `ib_write_bw` on shared links | R | Transfer p99 inflation; ECN/CNP/PFC counters | Router avoids congested rails if multi-rail; attributed in the report | Should |
| K10 | Coordinator crash | Any | Kill coordinator | R | Lease loss | In-flight transfers finish or time out; registry rebuilt; no leaked KV | Must |
| K11 | KV pool exhaustion on D | Reserve | Flood of long prompts | R | Reservation failure | Admission control rejects or queues; no OOM | Should |
| K12 | Prefill-side KV leak on abort | Abort | Any abort path | — | Leak detector on P's block allocator | Blocks freed within the stated bound | Must (test) |

## Gotchas Naresh must be able to explain

- **`tc netem` and iptables don't touch RDMA traffic** (kernel bypass). Use port state
  changes, competing RDMA traffic, or transport test hooks instead.
- **The retransmit horizon is finite and computable.** It is 4.096 µs × 2^timeout per
  attempt, times the retry count. It bounds how long a "dead" sender's WRITE can still
  land. Fencing by lease timeout alone must exceed it.
- **Heartbeat loss is not QP loss.** A decode worker can be alive while its QP is in ERR,
  and vice versa.
- **Failover after commit means recompute.** KV lived only on the dead D. Quantify this
  cost; it drives the case for KV replication, which is out of scope.
- **Every abort path must free blocks on both sides.** Leaks show up hours later as
  admission failures.
