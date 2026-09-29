"""Mirror of transport/include/kvwire/transport/transport.h. Keep the two in lockstep."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Protocol


class TransportStatus(str, enum.Enum):
    OK = "ok"
    UNIMPLEMENTED = "unimplemented"
    QP_ERROR = "qp_error"
    REMOTE_ACCESS_ERROR = "remote_access_error"
    STALE_EPOCH = "stale_epoch"
    FENCED = "fenced"
    TIMEOUT = "timeout"


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
