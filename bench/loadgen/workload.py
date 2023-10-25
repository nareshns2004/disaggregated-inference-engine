"""Workload definitions (EVALUATION §3): length distributions and arrival processes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LengthGrid:
    prompts: tuple[int, ...] = (512, 2048, 8192, 32768)
    outputs: tuple[int, ...] = (64, 256, 1024)


@dataclass(frozen=True, slots=True)
class Arrivals:
    kind: str  # "poisson" | "gamma"
    rate_rps: float
    cv: float = 1.0  # gamma burstiness; poisson == 1.0


# TODO(M1): trace loader (public conversation traces; record license + hash in the manifest).
