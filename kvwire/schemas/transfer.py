"""TransferDesc / TransferEvent. Plain dataclasses: zero dependencies, trivially serialisable."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class KvLayoutDesc:
    tp: int
    block_size: int
    dtype: str  # "bf16" | "fp16" | "fp8_e4m3" ...
    kv_layout: str  # "separate" | "interleaved"  (see kvwire.kvcalc.KvLayout)


@dataclass(frozen=True, slots=True)
class BlockRef:
    instance: str
    gpu: int
    blocks: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class TransferDesc:
    transfer_id: int
    epoch: int
    src: BlockRef
    dst: BlockRef
    layers: int
    bytes_per_layer: int
    layout: KvLayoutDesc
    # Exactly one of these is set by the receiver at reservation time (ADR-0005).
    rkey: int | None = None
    mw_handle: int | None = None
    version: int = SCHEMA_VERSION


class TransferEventKind(str, enum.Enum):
    ENQUEUED = "enqueued"
    LAYER_SENT = "layer_sent"
    COMMITTED = "committed"
    ABORTED = "aborted"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TransferEvent:
    transfer_id: int
    epoch: int
    kind: TransferEventKind
    ts_ns: int  # monotonic for durations; see RequestTimeline for cross-host correlation
    detail: dict[str, str] = field(default_factory=dict)
    version: int = SCHEMA_VERSION
