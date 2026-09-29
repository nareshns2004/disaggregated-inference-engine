"""Membership and health: heartbeats plus transport error reports.

Heartbeat loss is not QP loss (FAULT_MATRIX gotchas): a worker can be alive with its QP in ERR,
and vice versa. Track both signals separately.
"""

from __future__ import annotations

# TODO(M3): Membership with lease-based liveness and per-rail health (K05 flap damping).
