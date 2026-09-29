from __future__ import annotations

from kvwire.coordinator.registry import InMemoryRegistry
from kvwire.coordinator.state_machine import TransferState
from kvwire.schemas import BlockRef, KvLayoutDesc, TransferDesc


def _desc(tid: int = 1, epoch: int = 1) -> TransferDesc:
    return TransferDesc(
        transfer_id=tid,
        epoch=epoch,
        src=BlockRef("p0", 0, (1, 2)),
        dst=BlockRef("d0", 0, (7, 8)),
        layers=32,
        bytes_per_layer=128 * 1024,
        layout=KvLayoutDesc(tp=1, block_size=16, dtype="bf16", kv_layout="interleaved"),
    )


def test_stale_epoch_events_are_ignored() -> None:
    reg = InMemoryRegistry()
    reg.add(_desc(epoch=2), deadline_mono_ns=10)
    assert reg.transition(1, epoch=1, dst=TransferState.STREAMING) is False
    assert reg.get(1).state is TransferState.RESERVED
    assert reg.transition(1, epoch=2, dst=TransferState.STREAMING) is True
