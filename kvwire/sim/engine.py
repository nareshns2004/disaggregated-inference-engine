"""Discrete-event model of prefill/decode instances.

Purpose: exercise the coordinator's state machine, routing and fault handling on a laptop,
with injected faults, deterministic seeds and no GPU. It is NOT a performance model; never
quote its latencies as results.
"""

from __future__ import annotations

# TODO(M3): SimInstance(role, kv_blocks, prefill_tok_per_s, decode_step_s) with a virtual clock;
# SimTransport implementing kvwire.transport.Transport with injectable delay/drop/late-write.
