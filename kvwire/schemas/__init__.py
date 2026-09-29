"""Versioned cross-process schemas (ARCHITECTURE.md §5).

Bump SCHEMA_VERSION on any incompatible change and keep transport/include/kvwire/transport/types.h
(kSchemaVersion) in sync.
"""

from kvwire.schemas.fault import FaultInjection, FaultLabel
from kvwire.schemas.timeline import RequestOutcome, RequestTimeline
from kvwire.schemas.transfer import (
    SCHEMA_VERSION,
    BlockRef,
    KvLayoutDesc,
    TransferDesc,
    TransferEvent,
    TransferEventKind,
)

__all__ = [
    "SCHEMA_VERSION",
    "BlockRef",
    "FaultInjection",
    "FaultLabel",
    "KvLayoutDesc",
    "RequestOutcome",
    "RequestTimeline",
    "TransferDesc",
    "TransferEvent",
    "TransferEventKind",
]
