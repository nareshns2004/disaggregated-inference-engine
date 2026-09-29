"""FaultInjection record for the faultlab ground-truth ledger (FAULT_MATRIX.md)."""

from __future__ import annotations

import enum
from dataclasses import dataclass

from kvwire.schemas.transfer import SCHEMA_VERSION


class FaultLabel(str, enum.Enum):
    REAL = "real"
    INDUCED = "induced"  # real mechanism, triggered on purpose
    SYNTHETIC = "synthetic"


@dataclass(frozen=True, slots=True)
class FaultInjection:
    id: str
    fault_class: str  # FAULT_MATRIX id, e.g. "K07"
    label: FaultLabel
    target: str
    t_start_ns: int
    t_end_ns: int | None = None
    revert_ok: bool | None = None
    version: int = SCHEMA_VERSION
