# transport tests

| Label | Needs | Runs in CI |
|---|---|---|
| `unit` | nothing | yes |
| `rxe` | SoftRoCE device (`rdma link add rxe0 type rxe netdev <if>`), **non-performance** | later (self-hosted) |
| `gpu` | CUDA GPU + GPUDirect | no |
| `multinode` | two allowlisted hosts | no |

Planned M2 logic tests (write tests first; implementation is [OWNER-CORE]):
- QP lifecycle RESET→INIT→RTR→RTS, and Reset() after a forced ERR (K06) leaks nothing.
- K07: hold WRs, abort, Revoke(), reuse blocks, release WRs → late write gets
  `kRemoteAccessError`, and the reused block's bytes are unchanged.
- Idempotency: duplicate commit for committed/aborted epoch → `kStaleEpoch`, no state change.
- Per-rail commit counting with N QPs.
