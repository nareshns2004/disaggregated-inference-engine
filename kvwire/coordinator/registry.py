"""Transfer registry: transfer_id -> (P, D, blocks, epoch, state, deadline).

In-memory for now. Coordinator restart recovers from instance reports (ADR pending), so this
store is deliberately not the source of truth for block ownership — the instances are.
"""

from __future__ import annotations

from dataclasses import dataclass

from kvwire.coordinator.state_machine import TransferState, check_transition
from kvwire.schemas import TransferDesc


@dataclass(slots=True)
class TransferRecord:
    desc: TransferDesc
    state: TransferState
    deadline_mono_ns: int


class InMemoryRegistry:
    def __init__(self) -> None:
        self._records: dict[int, TransferRecord] = {}

    def add(self, desc: TransferDesc, deadline_mono_ns: int) -> TransferRecord:
        if desc.transfer_id in self._records:
            raise KeyError(f"duplicate transfer_id {desc.transfer_id}")
        rec = TransferRecord(desc, TransferState.RESERVED, deadline_mono_ns)
        self._records[desc.transfer_id] = rec
        return rec

    def get(self, transfer_id: int) -> TransferRecord:
        return self._records[transfer_id]

    def transition(self, transfer_id: int, epoch: int, dst: TransferState) -> bool:
        """Apply a transition. Events for a stale epoch are ignored (idempotency) -> False."""
        rec = self._records[transfer_id]
        if epoch != rec.desc.epoch:
            return False
        check_transition(rec.state, dst)
        rec.state = dst
        return True

    def expired(self, now_mono_ns: int) -> list[TransferRecord]:
        # TODO(M5): deadline must exceed the retransmit horizon if the lease is the fence.
        return [r for r in self._records.values() if r.deadline_mono_ns <= now_mono_ns]
