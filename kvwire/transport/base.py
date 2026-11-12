"""Mirror of transport/include/kvwire/transport/transport.h and status.h.

``TransportStatus`` must list exactly the C++ ``StatusCode`` values, in order;
``tests/unit/test_transport_parity.py`` enforces it.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Protocol


class TransportStatus(str, enum.Enum):
    OK = "ok"
    UNIMPLEMENTED = "unimplemented"
    INVALID_ARGUMENT = "invalid_argument"
    RESOURCE_EXHAUSTED = "resource_exhausted"  # SQ/CQ full, MR limit, block pool exhausted
    TIMEOUT = "timeout"
    QP_ERROR = "qp_error"  # QP moved to ERR; caller must fence affected transfers
    REMOTE_ACCESS_ERROR = "remote_access_error"  # the *desired* K07 outcome for a late write
    PORT_DOWN = "port_down"
    STALE_EPOCH = "stale_epoch"  # event for a non-current epoch; ignored (idempotent)
    FENCED = "fenced"  # transfer was aborted and fenced
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True)
class RemoteGrant:
    base_addr: int
    rkey: int
    transfer_id: int
    epoch: int


class Transport(Protocol):
    def send_layer(
        self,
        transfer_id: int,
        epoch: int,
        layer: int,
        src: list[tuple[int, int]],
        dst: list[tuple[int, int]],
        grant: RemoteGrant,
        last_layer: bool,
    ) -> TransportStatus: ...

    def abort(self, transfer_id: int, epoch: int) -> TransportStatus: ...

    def reserve(
        self, transfer_id: int, epoch: int, dst: list[tuple[int, int]]
    ) -> tuple[TransportStatus, RemoteGrant | None]: ...

    def release(self, transfer_id: int, epoch: int) -> TransportStatus:
        """Fence first, then free. After OK, no write of (transfer_id, epoch) can land."""
        ...
