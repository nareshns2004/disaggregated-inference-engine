"""Per-request timeline: the raw material for the TTFT decomposition (EVALUATION.md §1)."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from kvwire.schemas.transfer import SCHEMA_VERSION


class RequestOutcome(str, enum.Enum):
    OK = "ok"
    FAILED_FAST = "failed_fast"  # explicit error returned to client (counted separately)
    TIMEOUT = "timeout"
    REJECTED = "rejected"  # admission control


@dataclass(slots=True)
class RequestTimeline:
    """Timestamps are UTC epoch-ns (cross-host); clock-sync assumptions go in ENVIRONMENT.md."""

    req_id: str
    prompt_tokens: int
    output_tokens: int = 0
    prefill_instance: str | None = None
    decode_instance: str | None = None
    transfer_id: int | None = None
    ts_arrival: int | None = None
    ts_admit: int | None = None
    ts_prefill_start: int | None = None
    ts_prefill_end: int | None = None
    ts_layer_sent: list[int] = field(default_factory=list)
    ts_commit: int | None = None
    ts_first_token: int | None = None
    ts_tokens: list[int] = field(default_factory=list)
    ts_done: int | None = None
    outcome: RequestOutcome | None = None
    tokens_hash: str | None = None  # for the greedy correctness gate
    version: int = SCHEMA_VERSION
