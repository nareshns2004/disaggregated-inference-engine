"""Scenario model: which FAULT_MATRIX classes, when, on what target, how many trials."""

from __future__ import annotations

from dataclasses import dataclass, field

from kvwire.schemas import FaultLabel

MUST_CLASSES = ("K01", "K02", "K03", "K04", "K05", "K06", "K07", "K08", "K10", "K12")


@dataclass(frozen=True, slots=True)
class FaultSpec:
    fault_class: str
    label: FaultLabel
    target: str  # role or instance selector, resolved against the allowlist
    trials: int = 20  # EVALUATION §4: >= 20 per Must class
    at: str = "random"  # "random" (seeded) | phase name, e.g. "streaming"
    params: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    seed: int
    faults: tuple[FaultSpec, ...]
    revert_timeout_s: float = 30.0


def load(path: str) -> Scenario:
    """Parse YAML (needs the `bench` extra for PyYAML). TODO(M5)."""
    raise NotImplementedError("M5")
