from __future__ import annotations

from typing import Protocol


class Mechanism(Protocol):
    """Contract: `arm()` registers the revert; `inject()` acts; `revert()` is idempotent."""

    fault_class: str

    def arm(self) -> None: ...
    def inject(self) -> None: ...
    def revert(self) -> None: ...


# TODO(M5): ProcessKill (K01-K03, K10), PortDown/Flap (K04/K05), ForceQpError via transport
# test hook (K06), HeldWriteAbortReuse (K07), RecvDelay (K08), CompetingWriteBw (K09).
