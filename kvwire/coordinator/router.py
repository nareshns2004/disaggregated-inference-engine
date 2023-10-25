"""Routing / admission policy interface (Should: SLO-aware; ADR on policy pending)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class InstanceView:
    instance_id: str
    role: str  # "prefill" | "decode"
    healthy: bool
    queue_depth: int
    kv_free_blocks: int
    rails_healthy: int


@dataclass(frozen=True, slots=True)
class RouteDecision:
    admit: bool
    prefill: str | None = None
    decode: str | None = None
    reason: str = ""


class RoutingPolicy(Protocol):
    def route(self, prompt_tokens: int, instances: list[InstanceView]) -> RouteDecision: ...


# TODO(M3): a basic least-loaded policy. TODO(M5, OWNER-CORE): SLO-aware admission.
