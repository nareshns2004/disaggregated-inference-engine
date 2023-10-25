"""Transfer state machine (ARCHITECTURE.md §4.1).

The *table* of legal transitions is design and lives here as data. The abort / fence / retry
*handlers* are [OWNER-CORE] (MILESTONES M5) and are intentionally unimplemented.
"""

from __future__ import annotations

import enum


class TransferState(str, enum.Enum):
    RESERVED = "reserved"
    STREAMING = "streaming"
    COMMITTED = "committed"
    DECODING = "decoding"
    DONE = "done"
    ABORTED = "aborted"  # fenced: no write of this epoch can land any more
    RETRY = "retry"  # a new transfer (new epoch) replaces this one
    FAILED = "failed"  # fail fast with a clear error; never return garbage


TERMINAL: frozenset[TransferState] = frozenset(
    {TransferState.DONE, TransferState.FAILED, TransferState.RETRY}
)

LEGAL_TRANSITIONS: dict[TransferState, frozenset[TransferState]] = {
    TransferState.RESERVED: frozenset({TransferState.STREAMING, TransferState.ABORTED}),
    TransferState.STREAMING: frozenset({TransferState.COMMITTED, TransferState.ABORTED}),
    TransferState.COMMITTED: frozenset({TransferState.DECODING, TransferState.ABORTED}),
    TransferState.DECODING: frozenset({TransferState.DONE, TransferState.ABORTED}),
    TransferState.ABORTED: frozenset({TransferState.RETRY, TransferState.FAILED}),
    TransferState.DONE: frozenset(),
    TransferState.RETRY: frozenset(),
    TransferState.FAILED: frozenset(),
}


class IllegalTransitionError(Exception):
    pass


def check_transition(src: TransferState, dst: TransferState) -> None:
    if dst not in LEGAL_TRANSITIONS[src]:
        raise IllegalTransitionError(f"{src.value} -> {dst.value}")


# ---- [OWNER-CORE] M5: handlers. Signatures are proposals; change them with ARCHITECTURE.md. ----


def on_abort(transfer_id: int, epoch: int, reason: str) -> None:
    """Fence (Transport.release -> Fence.revoke) BEFORE any block returns to an allocator."""
    raise NotImplementedError("[OWNER-CORE] M5")


def on_retry(transfer_id: int, epoch: int) -> int:
    """Pick a new D (or recompute on P); return the new transfer's epoch (strictly greater)."""
    raise NotImplementedError("[OWNER-CORE] M5")
